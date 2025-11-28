# API 키 암호화 PowerShell 스크립트
# 사용법: .\encrypt_key.ps1

Write-Host "API 키 암호화 스크립트" -ForegroundColor Green
Write-Host ""

# cryptography 설치 확인
Write-Host "cryptography 모듈 확인 중..." -ForegroundColor Yellow
$cryptoCheck = python -c "import cryptography" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "cryptography 모듈이 설치되지 않았습니다. 설치 중..." -ForegroundColor Yellow
    python -m pip install cryptography
    if ($LASTEXITCODE -ne 0) {
        Write-Host "cryptography 설치에 실패했습니다." -ForegroundColor Red
        exit 1
    }
}

# API 키 입력
$apiKey = Read-Host "OpenAI API 키를 입력하세요"

if ([string]::IsNullOrWhiteSpace($apiKey)) {
    Write-Host "API 키가 입력되지 않았습니다." -ForegroundColor Red
    exit 1
}

# 암호화 실행
Write-Host ""
Write-Host "암호화 중..." -ForegroundColor Yellow
$encrypted = python key_manager.py encrypt $apiKey

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "암호화 완료!" -ForegroundColor Green
    Write-Host ""
    Write-Host "다음 단계:" -ForegroundColor Cyan
    Write-Host "1. .streamlit/secrets.toml 파일을 열고" -ForegroundColor White
    Write-Host "2. OPENAI_API_KEY 줄을 삭제하고" -ForegroundColor White
    Write-Host "3. 아래 암호화된 키를 추가하세요:" -ForegroundColor White
    Write-Host ""
    Write-Host $encrypted -ForegroundColor Yellow
} else {
    Write-Host "암호화에 실패했습니다." -ForegroundColor Red
    exit 1
}

