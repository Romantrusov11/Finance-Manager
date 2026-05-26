import base64
import io
import os
import time
import uuid
from datetime import datetime, timedelta

import pyotp
import qrcode
from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session

import models
import schemas
from database import Base, engine, get_db
from security import (
    create_access_token,
    get_current_user,
    get_current_user_allow_temp,
    hash_password,
    verify_password,
)

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Personal Finance Manager API", version="1.1.0")

REPORTS: dict[str, dict] = {}
REPORTS_DIR = "generated_reports"
os.makedirs(REPORTS_DIR, exist_ok=True)


@app.get("/")
def root():
    return {"message": "Personal Finance Manager API"}


@app.get("/status")
def get_status():
    return {"status": "ok", "message": "Server is running"}


@app.post("/auth/register", response_model=schemas.UserOut)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(models.User).filter(
        (models.User.username == user.username) | (models.User.email == user.email)
    ).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username or email already registered")

    db_user = models.User(
        username=user.username,
        email=user.email,
        password_hash=hash_password(user.password),
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@app.post("/auth/login", response_model=schemas.Token)
def login(user: schemas.UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if not db_user or not verify_password(user.password, db_user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect username or password")

    if db_user.totp_secret:
        temp_token = create_access_token(
            data={"sub": db_user.username, "temp": True},
            expires_delta=timedelta(minutes=5),
        )
        return {"access_token": temp_token, "token_type": "bearer", "requires_2fa": True}

    access_token = create_access_token(data={"sub": db_user.username})
    return {"access_token": access_token, "token_type": "bearer", "requires_2fa": False}


@app.get("/auth/setup-2fa", response_model=schemas.TOTPSecret)
def setup_2fa(current_user: models.User = Depends(get_current_user)):
    secret = pyotp.random_base32()
    uri = pyotp.TOTP(secret).provisioning_uri(
        name=current_user.username,
        issuer_name="Finance Manager",
    )
    img = qrcode.make(uri)
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    qr_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
    return {"secret": secret, "qr_url": qr_base64}


@app.post("/auth/enable-2fa")
def enable_2fa(
    req: schemas.Enable2FARequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    totp = pyotp.TOTP(req.secret)
    if not totp.verify(req.code):
        raise HTTPException(status_code=401, detail="Invalid code")
    current_user.totp_secret = req.secret
    db.commit()
    return {"message": "2FA enabled successfully"}


@app.post("/auth/verify-2fa", response_model=schemas.Token)
def verify_2fa(
    code: schemas.TwoFactorCode,
    current_user: models.User = Depends(get_current_user_allow_temp),
):
    if not current_user.totp_secret:
        raise HTTPException(status_code=400, detail="2FA not enabled for this user")
    totp = pyotp.TOTP(current_user.totp_secret)
    if not totp.verify(code.code):
        raise HTTPException(status_code=401, detail="Invalid 2FA code")
    access_token = create_access_token(data={"sub": current_user.username})
    return {"access_token": access_token, "token_type": "bearer", "requires_2fa": False}


@app.get("/transactions", response_model=list[schemas.TransactionOut])
def get_transactions(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(models.Transaction)
        .filter(models.Transaction.user_id == current_user.id)
        .order_by(models.Transaction.created_at.desc())
        .all()
    )


@app.post("/transactions", response_model=schemas.TransactionOut)
def create_transaction(
    data: schemas.TransactionCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    transaction = models.Transaction(
        amount=data.amount,
        category=data.category,
        description=data.description,
        user_id=current_user.id,
    )
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    return transaction


@app.put("/transactions/{transaction_id}", response_model=schemas.TransactionOut)
def update_transaction(
    transaction_id: int,
    data: schemas.TransactionUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    transaction = (
        db.query(models.Transaction)
        .filter(models.Transaction.id == transaction_id, models.Transaction.user_id == current_user.id)
        .first()
    )
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")

    if data.amount is not None:
        transaction.amount = data.amount
    if data.category is not None:
        transaction.category = data.category
    if data.description is not None:
        transaction.description = data.description

    db.commit()
    db.refresh(transaction)
    return transaction


@app.delete("/transactions/{transaction_id}")
def delete_transaction(
    transaction_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    transaction = (
        db.query(models.Transaction)
        .filter(models.Transaction.id == transaction_id, models.Transaction.user_id == current_user.id)
        .first()
    )
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")

    db.delete(transaction)
    db.commit()
    return {"message": "Transaction deleted successfully"}


@app.get("/statistics")
def get_statistics(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    transactions = db.query(models.Transaction).filter(models.Transaction.user_id == current_user.id).all()
    total_amount = sum(float(transaction.amount) for transaction in transactions)
    by_category: dict[str, float] = {}
    for transaction in transactions:
        by_category[transaction.category] = by_category.get(transaction.category, 0) + float(transaction.amount)
    return {
        "total_transactions": len(transactions),
        "total_amount": total_amount,
        "by_category": by_category,
    }


def generate_report_task(report_id: str, username: str, transactions_snapshot: list[dict]):
    REPORTS[report_id]["status"] = "processing"
    time.sleep(5)

    total_amount = sum(float(item["amount"]) for item in transactions_snapshot)
    by_category: dict[str, float] = {}
    for item in transactions_snapshot:
        by_category[item["category"]] = by_category.get(item["category"], 0) + float(item["amount"])

    report_path = os.path.join(REPORTS_DIR, f"{report_id}.txt")
    with open(report_path, "w", encoding="utf-8") as file:
        file.write("Personal Finance Manager Report\n")
        file.write("=" * 40 + "\n")
        file.write(f"User: {username}\n")
        file.write(f"Generated at: {datetime.now()}\n")
        file.write(f"Transactions count: {len(transactions_snapshot)}\n")
        file.write(f"Total amount: {total_amount:.2f}\n\n")
        file.write("By category:\n")
        for category, amount in by_category.items():
            file.write(f"- {category}: {amount:.2f}\n")
        file.write("\nTransactions:\n")
        for item in transactions_snapshot:
            file.write(f"#{item['id']} | {item['amount']} | {item['category']} | {item.get('description') or ''}\n")

    REPORTS[report_id]["status"] = "done"
    REPORTS[report_id]["file"] = report_path


@app.post("/reports/generate")
def generate_report(
    background_tasks: BackgroundTasks,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    transactions = db.query(models.Transaction).filter(models.Transaction.user_id == current_user.id).all()
    transactions_snapshot = [
        {
            "id": transaction.id,
            "amount": transaction.amount,
            "category": transaction.category,
            "description": transaction.description,
            "created_at": str(transaction.created_at),
        }
        for transaction in transactions
    ]

    report_id = str(uuid.uuid4())
    REPORTS[report_id] = {"status": "created", "file": None}
    background_tasks.add_task(generate_report_task, report_id, current_user.username, transactions_snapshot)
    return {"message": "Report generation started", "report_id": report_id, "status": "created"}


@app.get("/reports/{report_id}")
def get_report_status(report_id: str, current_user: models.User = Depends(get_current_user)):
    report = REPORTS.get(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return {"report_id": report_id, "status": report["status"], "file": report["file"]}
