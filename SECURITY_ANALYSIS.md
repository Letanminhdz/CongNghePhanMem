# 🔐 SECURITY ANALYSIS - Authentication & Authorization

**Date:** May 26, 2026  
**Severity Summary:** 🔴 **CRITICAL** issues found + ⚠️ HIGH + ℹ️ MEDIUM

---

## 1️⃣ CORE SECURITY CONFIGURATION

### File: [core/config.py](backend/app/core/config.py)

#### JWT Configuration
```python
SECRET_KEY: str = secrets.token_urlsafe(32)
# BUT: Falls back to DEFAULT "changethis" if not in .env
# Location: Line 48-49

ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days = 11,520 minutes
# ⚠️ ISSUE: Token expiration is 8 DAYS (very long!)
```

#### Hardcoded Superuser Credentials
```python
FIRST_SUPERUSER: EmailStr = "admin@example.com"
FIRST_SUPERUSER_PASSWORD: str = "changethis"  # Line 116 ❌ HARDCODED
```

#### Security Validation
```python
@model_validator(mode="after")
def _enforce_non_default_secrets(self) -> Self:
    self._check_default_secret("SECRET_KEY", self.SECRET_KEY)
    self._check_default_secret("POSTGRES_PASSWORD", self.POSTGRES_PASSWORD)
    self._check_default_secret("FIRST_SUPERUSER_PASSWORD", self.FIRST_SUPERUSER_PASSWORD)
    return self
    # ✅ GOOD: Validates default secrets, but only WARNS in local env
    # ❌ BAD: Allows "changethis" in development - developers may forget to change
```

---

## 2️⃣ PASSWORD HASHING & VERIFICATION

### File: [core/security.py](backend/app/core/security.py)

#### Password Hashing
```python
ALGORITHM = "HS256"  # ✅ GOOD: Standard JWT algorithm

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
# ✅ EXCELLENT: Using bcrypt with auto-upgrade on deprecated algorithms

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)
    # ✅ GOOD: Secure verification using passlib

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)
    # ✅ GOOD: Password hashing using bcrypt
```

#### JWT Token Creation
```python
def create_access_token(subject: str | Any, expires_delta: timedelta | None = None) -> str:
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
    
# ✅ GOOD: Includes expiration AND subject (user ID)
# ✅ GOOD: Uses secrets for signing
# ❌ ISSUE: No "iat" (issued at) claim - not best practice
# ❌ ISSUE: No "jti" (JWT ID) for token revocation
```

---

## 3️⃣ DEPENDENCY INJECTION & AUTHENTICATION

### File: [api/deps.py](backend/app/api/deps.py)

#### Database Session Dependency
```python
def get_db() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_db)]
# ✅ GOOD: Proper database session management
```

#### OAuth2 Bearer Token
```python
reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/login/access-token"
)
# ✅ GOOD: Standard OAuth2 pattern
```

#### Current User Extraction
```python
def get_current_user(session: SessionDep, token: TokenDep) -> User:
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[security.ALGORITHM]
        )
        token_data = TokenPayload(**payload)
    except (InvalidTokenError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )
    user = session.get(User, token_data.sub)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return user

CurrentUser = Annotated[User, Depends(get_current_user)]
# ✅ GOOD: Validates token and checks user status
# ❌ BUG: Tries to access user.is_active but uses session.get(User, pk) which doesn't work with SessionModel
# ✅ GOOD: Checks if user is active
```

#### Superuser Check
```python
def get_current_active_superuser(current_user: CurrentUser) -> User:
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=403, detail="The user doesn't have enough privileges"
        )
    return current_user

# ❌ CRITICAL BUG: Field 'is_superuser' DOES NOT EXIST in User model!
# This will cause AttributeError at runtime
```

---

## 4️⃣ LOGIN ENDPOINT

### File: [api/v1/endpoints/auth.py](backend/app/api/v1/endpoints/auth.py)

#### Login Flow
```python
@router.post("/login/access-token", response_model=Token)
def login_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Session = Depends(get_db),
):
    """OAuth2 compatible token login, retrieve an access token for future requests."""
    
    user = user_repository.authenticate_user(
        db, email=form_data.username, password=form_data.password
    )
    
    if not user:
        logger.warning(f"Failed login attempt for email={form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    elif not user.is_active:
        logger.warning(f"Inactive user login attempt for user_id={user.id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user",
        )
    
    access_token = create_access_token(
        subject=str(user.id),
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    logger.info(f"Successful login for user_id={user.id}")
    return Token(access_token=access_token, token_type="bearer")

# ✅ GOOD: Log failed login attempts
# ✅ GOOD: Check if user is active
# ⚠️ MEDIUM: Generic error message (good for security, but users like clarity)
# ❌ ISSUE: No rate limiting on login attempts (brute force vulnerability)
# ❌ ISSUE: No account lockout after N failed attempts
# ❌ ISSUE: No refresh token mechanism
```

---

## 5️⃣ SIGNUP ENDPOINT

### File: [api/v1/endpoints/users.py](backend/app/api/v1/endpoints/users.py)

#### User Signup
```python
@router.post("/signup", response_model=UserRead, status_code=201)
def signup(user_in: UserCreate, db: Session = Depends(get_db)):
    """Compatibility endpoint for frontend: /users/signup"""
    
    existing = user_repository.get_user_by_email(db, email=user_in.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    
    user = user_repository.create_user(db, user_in=user_in)
    logger.info("New user registered user_id=%s, email=%s", user.id, user.email)
    return user

# ✅ GOOD: Check for duplicate email
# ✅ GOOD: Log new registrations
# ⚠️ MEDIUM: No email verification before activation
# ⚠️ MEDIUM: No password strength validation
# ⚠️ MEDIUM: No email validation (only EmailStr Pydantic check)
# ⚠️ MEDIUM: New users are immediately active (should require email confirmation)
```

#### Input Validation
```python
# From schemas/user.py
class UserCreate(UserBase):
    password: str

# ❌ NO PASSWORD VALIDATION:
# - No minimum length requirement
# - No complexity requirements (uppercase, numbers, special chars)
# - No common password check
```

---

## 6️⃣ PASSWORD RESET FLOW

### File: [api/v1/endpoints/auth.py](backend/app/api/v1/endpoints/auth.py)

#### Forget Password Request
```python
@router.post("/forgot-password", response_model=PasswordResetResponse)
def forgot_password(
    request: ForgotPasswordRequest,
    db: Session = Depends(get_db),
):
    user = user_repository.get_user_by_email(db, email=request.email)
    if user:
        token = generate_password_reset_token(user.email)
        logger.info(f"Reset token for {user.email}: {token}")  # ❌ LOGS THE TOKEN!
        
        if settings.emails_enabled:
            email_data = generate_reset_password_email(
                email_to=user.email,
                email=user.email,
                token=token,
            )
            try:
                send_email(
                    email_to=user.email,
                    subject=email_data.subject,
                    html_content=email_data.html_content,
                )
            except Exception as exc:
                logger.warning(f"Password reset email could not be sent: {exc}")
    
    # Always return success message for security
    return PasswordResetResponse(
        message="If that email is registered, we sent a password recovery link"
    )

# ⚠️ CRITICAL: logger.info() LOGS THE ACTUAL RESET TOKEN!
#             This is a serious information disclosure vulnerability
# ✅ GOOD: Returns success regardless of email existence (enumeration protection)
```

#### Reset Password
```python
@router.post("/reset-password", response_model=PasswordResetResponse)
def reset_password(
    request: ResetPasswordRequest,
    db: Session = Depends(get_db),
):
    email = verify_password_reset_token(request.token)
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid token"
        )
    
    user = user_repository.get_user_by_email(db, email=email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user_repository.update_user_password(db, user, request.new_password)
    logger.info(f"Password reset success for user_id={user.id}")
    return PasswordResetResponse(message="Password updated successfully")

# ✅ GOOD: Validates reset token
# ✅ GOOD: Logs success
# ⚠️ MEDIUM: No new password strength validation
# ❌ MEDIUM: Token is used once but not invalidated in database
#            (depends on JWT expiration only)
```

#### Password Reset Token Generation
```python
# From app/utils.py
def generate_password_reset_token(email: str) -> str:
    delta = timedelta(hours=settings.EMAIL_RESET_TOKEN_EXPIRE_HOURS)  # default 48
    now = datetime.now(timezone.utc)
    expires = now + delta
    exp = expires.timestamp()
    
    encoded_jwt = jwt.encode(
        {"exp": exp, "nbf": now, "sub": email},
        settings.SECRET_KEY,
        algorithm=security.ALGORITHM,
    )
    return encoded_jwt

# ✅ GOOD: Uses JWT with expiration (default 48 hours)
# ✅ GOOD: Uses secure SECRET_KEY
# ✅ GOOD: Includes nbf (not before) claim
# ✅ GOOD: Expires in reasonable time

def verify_password_reset_token(token: str) -> str | None:
    try:
        decoded_token = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[security.ALGORITHM]
        )
        return str(decoded_token["sub"])
    except InvalidTokenError:
        return None

# ✅ GOOD: Validates token signature
# ✅ GOOD: Handles invalid tokens gracefully
```

---

## 7️⃣ USER MODEL

### File: [models/user.py](backend/app/models/user.py)

```python
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

# ✅ GOOD: Email is unique and indexed
# ✅ GOOD: Password is hashed (stored as STRING for bcrypt hash)
# ✅ GOOD: is_active flag for user suspension
# ✅ GOOD: created_at timestamp
# ❌ MISSING: is_superuser field (referenced in deps.py but doesn't exist!)
# ⚠️ MISSING: last_login timestamp
# ⚠️ MISSING: password_changed_at timestamp
# ⚠️ MISSING: failed_login_attempts counter
# ⚠️ MISSING: locked_until timestamp for rate limiting
```

---

## 8️⃣ HARDCODED SECRETS & CREDENTIALS

### File: [.env](/.env)

```bash
# ❌ CRITICAL: SECRET_KEY hardcoded
SECRET_KEY=changethis

# ❌ CRITICAL: DEFAULT SUPERUSER PASSWORD
FIRST_SUPERUSER=admin@example.com
FIRST_SUPERUSER_PASSWORD=admin123  # ❌ EXPOSED IN .env

# ❌ CRITICAL: DATABASE PASSWORD
POSTGRES_PASSWORD=changethis

# ❌ CRITICAL: NEO4J CREDENTIALS EXPOSED
NEO4J_URI=neo4j+s://3e08ff89.databases.neo4j.io
NEO4J_USERNAME=3e08ff89
NEO4J_PASSWORD=wV2TnpvJD3DiQpQbTogvX8WdmOPfrarOdWyVN_d1Es0
```

### Issues:
- ❌ `.env` file should NEVER be committed to git
- ❌ All credentials are plaintext
- ❌ Database credentials exposed
- ❌ Neo4j credentials exposed publicly
- ❌ Default passwords used in development

---

## 9️⃣ AUTHENTICATION MIDDLEWARE ISSUES

### Detected Problems:

#### 1. **BUG: Missing `is_superuser` Field**
```python
# In deps.py - Line 53
def get_current_active_superuser(current_user: CurrentUser) -> User:
    if not current_user.is_superuser:  # ❌ Field doesn't exist!
        raise HTTPException(...)

# In models/user.py - FIELD IS MISSING
# User model has NO is_superuser attribute
```
**Impact:** Any endpoint using `get_current_active_superuser` will crash with `AttributeError`

#### 2. **No Session Type Support**
```python
# In deps.py - Line 49
user = session.get(User, token_data.sub)

# ❌ ISSUE: session.get() expects SQLAlchemy Session
# But code uses SessionModel/SQLModel which may need different approach
```

#### 3. **No CSRF Protection**
- No CSRF tokens on state-changing endpoints
- POST endpoints don't validate origin

#### 4. **No Rate Limiting**
- Login endpoint has no rate limiting
- Vulnerable to brute force attacks
- Reset password endpoint has no rate limiting

#### 5. **No Refresh Token**
- Access tokens valid for 8 days
- No way to revoke tokens without waiting for expiration
- No refresh token rotation

---

## 🔟 PASSWORD VALIDATION ISSUES

### No Password Requirements

```python
# Signup accepts ANY password
@router.post("/signup", response_model=UserRead, status_code=201)
def signup(user_in: UserCreate, db: Session = Depends(get_db)):
    # user_in.password is validated ONLY if it exists (required field)
    # NO strength validation!
    
# Acceptable passwords today:
✅ "a"         # 1 character!
✅ "123"       # Numbers only
✅ "abc"       # Lowercase only
✅ "password"  # Common password
```

---

## 📊 SECURITY SUMMARY TABLE

| Issue | Severity | Category | Status |
|-------|----------|----------|--------|
| Hardcoded `SECRET_KEY=changethis` in .env | 🔴 CRITICAL | Secrets | Active |
| Hardcoded superuser password in config.py | 🔴 CRITICAL | Secrets | Active |
| Neo4j credentials exposed in .env | 🔴 CRITICAL | Secrets | Active |
| Missing `is_superuser` field in User model | 🔴 CRITICAL | Bug | Active |
| Reset token logged in clear text | 🔴 CRITICAL | Information Disclosure | Active |
| No password strength validation | ⚠️ HIGH | Weak Passwords | Active |
| No rate limiting on login | ⚠️ HIGH | Brute Force | Active |
| 8-day token expiration | ⚠️ HIGH | Long TTL | Active |
| No email verification on signup | ⚠️ MEDIUM | Enumeration | Active |
| No refresh token mechanism | ⚠️ MEDIUM | Token Management | Active |
| No account lockout on failed login | ⚠️ MEDIUM | Brute Force | Active |
| No CSRF protection | ⚠️ MEDIUM | CSRF | Active |
| No "iat" claim in JWT | ℹ️ LOW | Best Practice | Active |
| No "jti" claim for token revocation | ℹ️ LOW | Token Management | Active |

---

## 🎯 REMEDIATION RECOMMENDATIONS

### IMMEDIATE (Critical - Fix Before Production)

1. **Fix Missing `is_superuser` Field**
   ```python
   # In models/user.py
   is_superuser = Column(Boolean, default=False)
   ```

2. **Remove Token Logging**
   ```python
   # In api/v1/endpoints/auth.py - forgot_password()
   # DELETE: logger.info(f"Reset token for {user.email}: {token}")
   ```

3. **Generate Secure SECRET_KEY**
   ```bash
   # In .env
   SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
   ```

4. **Use Environment Variables for Secrets**
   ```bash
   # Never hardcode passwords in code or .env
   SECRET_KEY=<generated-secure-key>
   FIRST_SUPERUSER_PASSWORD=<strong-random-password>
   POSTGRES_PASSWORD=<strong-random-password>
   ```

5. **Add .gitignore Entry**
   ```
   # Ensure .env is not committed
   .env
   .env.local
   .env.*.local
   ```

### HIGH PRIORITY

6. **Add Password Validation**
   ```python
   # Create validators/password.py
   def validate_password_strength(password: str) -> bool:
       if len(password) < 12:
           raise ValueError("Password must be at least 12 characters")
       if not any(c.isupper() for c in password):
           raise ValueError("Password must contain uppercase letter")
       if not any(c.isdigit() for c in password):
           raise ValueError("Password must contain digit")
       if not any(c in "!@#$%^&*" for c in password):
           raise ValueError("Password must contain special character")
   ```

7. **Add Rate Limiting**
   ```python
   # Install: pip install slowapi
   from slowapi import Limiter
   from slowapi.util import get_remote_address
   
   limiter = Limiter(key_func=get_remote_address)
   
   @router.post("/login/access-token")
   @limiter.limit("5/minute")
   def login_access_token(...):
       ...
   ```

8. **Reduce Token Expiration**
   ```python
   # In config.py
   ACCESS_TOKEN_EXPIRE_MINUTES: int = 60  # 1 hour instead of 8 days
   ```

9. **Add Refresh Token Support**
   ```python
   # Generate short-lived access tokens + long-lived refresh tokens
   REFRESH_TOKEN_EXPIRE_DAYS: int = 30
   ```

10. **Add Email Verification**
    ```python
    # Require email confirmation before signup activation
    is_email_verified = Column(Boolean, default=False)
    ```

---

## ✅ SECURITY CHECKLIST FOR PRODUCTION

- [ ] Remove all hardcoded secrets
- [ ] Add `is_superuser` field to User model
- [ ] Fix reset token logging
- [ ] Implement password strength validation
- [ ] Add rate limiting to auth endpoints
- [ ] Reduce token expiration time
- [ ] Add refresh token mechanism
- [ ] Implement email verification
- [ ] Enable HTTPS only
- [ ] Set secure cookies (if using)
- [ ] Add CORS restrictions
- [ ] Enable HTTPS redirect
- [ ] Review all logs for credential leaks
- [ ] Add account lockout mechanism
- [ ] Implement audit logging

---

**Generated:** 2026-05-26
