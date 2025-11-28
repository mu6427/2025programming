# API 키 암호화 가이드

## 문제 해결
GitHub의 secret scanning이 API 키를 감지하여 push가 차단되었습니다. 키를 암호화하여 해결하세요.

## 해결 방법

### 1. 기존 커밋에서 키 제거 (중요!)

먼저 git history에서 평문 키를 제거해야 합니다:

```powershell
# git filter-branch를 사용하여 history에서 제거
git filter-branch --force --index-filter "git rm --cached --ignore-unmatch .streamlit/secrets.toml" --prune-empty --tag-name-filter cat -- --all

# 또는 BFG Repo-Cleaner 사용 (더 빠름)
# https://rtyley.github.io/bfg-repo-cleaner/
```

### 2. API 키 암호화

1. **의존성 설치:**
   ```powershell
   pip install -r requirements.txt
   ```

2. **API 키 암호화:**
   ```powershell
   python key_manager.py encrypt "your-api-key-here"
   ```

3. **암호화된 키를 secrets.toml에 저장:**
   `.streamlit/secrets.toml` 파일을 열고:
   ```toml
   OPENAI_API_KEY_ENCRYPTED = "암호화된_키_여기에_입력"
   ```

### 3. .gitignore 확인

`.gitignore` 파일에 다음이 포함되어 있는지 확인:
```
.streamlit/secrets.toml
```

### 4. 새로운 커밋 생성

```powershell
git add .gitignore key_manager.py app.py requirements.txt
git commit -m "API 키 암호화 기능 추가"
git push
```

## 보안 권장사항

1. **환경 변수 사용 (권장):**
   ```powershell
   $env:OPENAI_API_KEY = "your-api-key"
   ```

2. **암호화 비밀번호 변경:**
   `key_manager.py`의 기본 비밀번호를 변경하거나 환경 변수로 설정:
   ```powershell
   $env:ENCRYPTION_PASSWORD = "your-strong-password"
   ```

3. **Streamlit Cloud 사용 시:**
   Streamlit Cloud의 Secrets 기능을 사용하면 자동으로 암호화됩니다.

## 키 복호화 테스트

```powershell
python key_manager.py decrypt "encrypted-key-here"
```

