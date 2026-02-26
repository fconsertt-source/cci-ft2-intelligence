# run_windows_friendly.ps1
# =============================================
# 🚀 سكربت تشغيل نظام CCI-FT2 (متوافق مع Windows)
# =============================================

# إعدادات الألوان
$Green = "Green"
$Yellow = "Yellow" 
$Red = "Red"
$Cyan = "Cyan"
$Magenta = "Magenta"
$White = "White"
$Gray = "Gray"

function Show-Banner {
    Write-Host "`n"
    Write-Host "    " -NoNewline
    Write-Host "==============================================" -ForegroundColor Cyan
    Write-Host "    " -NoNewline
    Write-Host "    نظام مراقبة سلسلة التبريد - CCI-FT2" -ForegroundColor White
    Write-Host "    " -NoNewline  
    Write-Host "    Intelligent Cold Chain Monitoring" -ForegroundColor Yellow
    Write-Host "    " -NoNewline
    Write-Host "==============================================" -ForegroundColor Cyan
    Write-Host "`n"
}

function Show-Step {
    param([string]$Message, [int]$Step)
    Write-Host "`n[$Step] " -NoNewline -ForegroundColor $Magenta
    Write-Host $Message -ForegroundColor $White
    Write-Host ("-" * 70) -ForegroundColor DarkGray
}

function Show-Success {
    param([string]$Message)
    Write-Host "[+] " -NoNewline -ForegroundColor $Green
    Write-Host $Message -ForegroundColor $Gray
}

function Show-Warning {
    param([string]$Message)
    Write-Host "[!] " -NoNewline -ForegroundColor $Yellow
    Write-Host $Message -ForegroundColor $Gray
}

function Show-Error {
    param([string]$Message)
    Write-Host "[X] " -NoNewline -ForegroundColor $Red
    Write-Host $Message -ForegroundColor $Gray
}

function Show-Info {
    param([string]$Message)
    Write-Host "[i] " -NoNewline -ForegroundColor $Cyan
    Write-Host $Message -ForegroundColor $Gray
}

# =============================================
# الدوال الرئيسية
# =============================================

function Run-MainPipeline {
    Show-Step "تشغيل خط المعالجة الرئيسي" 1
    
    Show-Info "جاري تشغيل نظام Python..."
    
    # تشغيل نظام المعالجة
    $pythonOutput = python -m scripts.run_ft2_pipeline 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        Show-Success "اكتملت معالجة البيانات"
        
        # البحث عن إحصائيات في الناتج
        if ($pythonOutput -match "الملفات المعالجة: (\d+) من أصل (\d+)") {
            $processed = $matches[1]
            $total = $matches[2]
            Show-Info "الملفات المعالجة: $processed/$total"
        }
        
    } else {
        Show-Error "فشل معالجة البيانات"
        Show-Warning "الناتج: $pythonOutput"
    }
}

function Check-Results {
    Show-Step "فحص النتائج" 2
    
    $reportPath = "data/output/centers_report.tsv"
    
    if (Test-Path $reportPath) {
        Show-Success "تم العثور على التقرير"
        
        # قراءة التقرير
        $lines = Get-Content $reportPath
        
        Write-Host "`n" -NoNewline
        Write-Host "نتائج التحليل:" -ForegroundColor Cyan
        Write-Host ("=" * 60) -ForegroundColor DarkGray
        
        # تخطي الرأس وعرض البيانات
        $dataLines = $lines | Select-Object -Skip 1
        
        foreach ($line in $dataLines) {
            $fields = $line -split "`t"
            
            if ($fields.Count -ge 3) {
                $center = $fields[1]
                $decision = $fields[2]
                
                # تحديد الرمز واللون
                if ($decision -like "*ACCEPTED*") {
                    $symbol = "[+]"
                    $color = $Green
                } elseif ($decision -like "*WARNING*") {
                    $symbol = "[!]"
                    $color = $Yellow
                } elseif ($decision -like "*REJECTED*") {
                    $symbol = "[X]"
                    $color = $Red
                } else {
                    $symbol = "[?]"
                    $color = $Gray
                }
                
                Write-Host " $symbol " -NoNewline -ForegroundColor $color
                Write-Host $center -NoNewline -ForegroundColor $White
                Write-Host " -> " -NoNewline -ForegroundColor $Gray
                Write-Host $decision -ForegroundColor $color
            }
        }
        
        Write-Host ("=" * 60) -ForegroundColor DarkGray
        
        # عرض إحصائيات
        $totalCenters = $dataLines.Count
        $accepted = ($dataLines | Where-Object { $_ -like "*ACCEPTED*" }).Count
        $warnings = ($dataLines | Where-Object { $_ -like "*WARNING*" }).Count
        $rejected = ($dataLines | Where-Object { $_ -like "*REJECTED*" }).Count
        
        Write-Host "`nالملخص:" -ForegroundColor Cyan
        Write-Host "  [+] سليمة: $accepted مركز" -ForegroundColor $Green
        Write-Host "  [!] تحذير: $warnings مركز" -ForegroundColor $Yellow
        Write-Host "  [X] مرفوضة: $rejected مركز" -ForegroundColor $Red
        Write-Host "  [Σ] الإجمالي: $totalCenters مركز" -ForegroundColor $White
        
        # عرض مسار الملف
        $fullPath = Resolve-Path $reportPath
        Write-Host "`nمسار التقرير: $fullPath" -ForegroundColor $Gray
        
    } else {
        Show-Error "لم يتم العثور على التقرير"
        
        # اقتراح إنشاء بيانات اختبار
        Show-Info "جرب إنشاء بيانات اختبار أولاً:"
        Write-Host "  python -m scripts.run_ft2_pipeline --generate-data" -ForegroundColor White
    }
}

function Create-TestData {
    Show-Step "إنشاء بيانات اختبار جديدة" 3
    
    Show-Info "جاري إنشاء بيانات اختبار..."
    
    # تشغيل مع خيار generate-data
    $pythonOutput = python -m scripts.run_ft2_pipeline --generate-data 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        Show-Success "تم إنشاء بيانات الاختبار"
    } else {
        Show-Error "فشل إنشاء بيانات الاختبار"
    }
}

function Generate-PDFReport {
    Show-Step "إنشاء تقرير PDF رسمي" 4
    
    Show-Info "جاري إنشاء تقرير PDF رسمي..."
    
    # التحقق من وجود التقرير أولاً
    if (-not (Test-Path "data/output/centers_report.tsv")) {
        Show-Warning "لا يوجد تقرير لتحويله إلى PDF"
        return
    }
    
    # استخدام المولد العربي المُصلح
    $pdfGenerator = Join-Path "src" "reporting" "arabic_pdf_generator.py"
    
    if (Test-Path $pdfGenerator) {
        try {
            # تغيير ترميز الكونسول مؤقتاً لـ Windows
            $originalEncoding = [Console]::OutputEncoding
            [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
            
            # تشغيل مولد PDF
            $pythonOutput = python $pdfGenerator 2>&1
            
            # إعادة الترميز الأصلي
            [Console]::OutputEncoding = $originalEncoding
            
            if ($LASTEXITCODE -eq 0) {
                Show-Success "تم إنشاء تقرير PDF رسمي بالعربية"
                
                $pdfPath = "data/output/reports/cold_chain_official_report.pdf"
                if (Test-Path $pdfPath) {
                    $fullPath = Resolve-Path $pdfPath
                    Write-Host "  [+] تم إنشاء الملف: $fullPath" -ForegroundColor Green
                    
                    # عرض إحصائيات بسيطة
                    $data = Import-Csv "data/output/centers_report.tsv" -Delimiter "`t"
                    $total = $data.Count
                    $rejected = ($data | Where-Object { $_.decision -like "*REJECTED*" }).Count
                    $accepted = ($data | Where-Object { $_.decision -like "*ACCEPTED*" }).Count
                    $warning = ($data | Where-Object { $_.decision -like "*WARNING*" }).Count
                    
                    Write-Host "  [i] إحصائيات التقرير:" -ForegroundColor Cyan
                    Write-Host "      - إجمالي المراكز: $total" -ForegroundColor White
                    Write-Host "      - مقبولة: $accepted" -ForegroundColor Green
                    Write-Host "      - تحت المراقبة: $warning" -ForegroundColor Yellow
                    Write-Host "      - مرفوضة: $rejected" -ForegroundColor Red
                    
                    # اقتراح فتح الملف
                    Write-Host "`n  [i] لفتح التقرير، استخدم الأمر:" -ForegroundColor Cyan
                    Write-Host "      Start-Process `"$fullPath`"" -ForegroundColor White
                }
            } else {
                Show-Error "فشل إنشاء PDF"
                if ($pythonOutput) {
                    Write-Host "  [DEBUG] تفاصيل الخطأ:" -ForegroundColor Gray
                    Write-Host $pythonOutput -ForegroundColor Gray
                }
            }
        } catch {
            Show-Warning "فشل إنشاء PDF: $_"
        }
    } else {
        Show-Warning "المولد العربي غير متوفر"
        Show-Info "جاري استخدام المولد البسيط..."
        
        # استخدام المولد القديم كبديل
        if (Test-Path "src/reporting/simple_pdf_generator.py") {
            python -c "from src.reporting.simple_pdf_generator import create_simple_pdf; create_simple_pdf()"
        }
    }
}

function Open-ResultsFolder {
    Show-Step "فتح مجلد النتائج" 5
    
    $outputFolder = "data/output"
    
    if (Test-Path $outputFolder) {
        Start-Process "explorer.exe" -ArgumentList (Resolve-Path $outputFolder)
        Show-Success "تم فتح مجلد النتائج"
    } else {
        Show-Warning "مجلد النتائج غير موجود"
    }
}

# =============================================
# القائمة الرئيسية
# =============================================
function Show-Menu {
    Clear-Host
    Show-Banner
    
    Write-Host "اختر خياراً:" -ForegroundColor White
    Write-Host ("─" * 40) -ForegroundColor DarkGray
    
    Write-Host "1. " -NoNewline -ForegroundColor $Cyan
    Write-Host "تشغيل النظام كاملاً" -ForegroundColor $White
    
    Write-Host "2. " -NoNewline -ForegroundColor $Cyan
    Write-Host "إنشاء بيانات اختبار جديدة" -ForegroundColor $White
    
    Write-Host "3. " -NoNewline -ForegroundColor $Cyan
    Write-Host "عرض النتائج فقط" -ForegroundColor $White
    
    Write-Host "4. " -NoNewline -ForegroundColor $Cyan
    Write-Host "إنشاء تقرير PDF" -ForegroundColor $White
    
    Write-Host "5. " -NoNewline -ForegroundColor $Cyan
    Write-Host "فتح مجلد النتائج" -ForegroundColor $White
    
    Write-Host "6. " -NoNewline -ForegroundColor $Cyan
    Write-Host "تشغيل جميع الاختبارات (Pytest)" -ForegroundColor $White
    
    Write-Host "0. " -NoNewline -ForegroundColor $Red
    Write-Host "خروج" -ForegroundColor $White
    
    Write-Host ("─" * 40) -ForegroundColor DarkGray
}

# =============================================
# البرنامج الرئيسي
# =============================================
function Main {
    do {
        Show-Menu
        
        $choice = Read-Host "`nاختيارك"
        
        switch ($choice) {
            "1" {
                # تشغيل كامل
                Run-MainPipeline
                Check-Results
                Generate-PDFReport
                Open-ResultsFolder
            }
            "2" {
                # إنشاء بيانات اختبار
                Create-TestData
            }
            "3" {
                # عرض النتائج فقط
                Check-Results
            }
            "4" {
                # إنشاء PDF
                Generate-PDFReport
            }
            "5" {
                # فتح المجلد
                Open-ResultsFolder
            }
            "6" {
                # تشغيل الاختبارات
                Show-Step "تشغيل جميع الاختبارات (Pytest)" 6
                
                # التأكد من أن Python و Pytest مثبتان
                $pythonExists = (Get-Command python -ErrorAction SilentlyContinue)
                if (-not $pythonExists) {
                    Show-Error "لم يتم العثور على Python. يرجى تثبيته وإضافته إلى PATH."
                    return
                }
                
                $pytestExists = (python -m pip show pytest)
                if ($LASTEXITCODE -ne 0) {
                    Show-Warning "Pytest غير مثبت. جار محاولة التثبيت..."
                    python -m pip install pytest
                    if ($LASTEXITCODE -ne 0) {
                        Show-Error "فشل تثبيت Pytest. يرجى تثبيته يدوياً: pip install pytest"
                        return
                    }
                    Show-Success "تم تثبيت Pytest بنجاح."
                }
                
                Show-Info "جاري تشغيل Pytest..."
                
                # تشغيل pytest
                pytest
                
                if ($LASTEXITCODE -eq 0) { 
                    Show-Success "نجحت جميع الاختبارات" 
                } else { 
                    Show-Error "فشلت بعض الاختبارات" 
                }
            }
            "0" {
                Write-Host "`nمع السلامة!" -ForegroundColor Green
                return
            }
            default {
                Write-Host "خيار غير صحيح" -ForegroundColor Red
            }
        }
        
        if ($choice -ne "0") {
            Write-Host "`n"
            Write-Host "اضغط أي مفتاح للمتابعة..." -ForegroundColor Gray
            $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
        }
        
    } while ($choice -ne "0")
}

# =============================================
# بدء التشغيل
# =============================================
if ($MyInvocation.InvocationName -ne '.') {
    try {
        Main
    } catch {
        Write-Host "خطأ غير متوقع: $_" -ForegroundColor Red
    }
}