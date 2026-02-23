# Seven AI v2.0 - Distribution Checklist

Use this checklist before public release to ensure quality and safety.

---

## ✅ PRE-FLIGHT CHECKLIST

### Phase 1: Code Sanitization

- [x] **Personal Data Removed**
  - [x] USER_NAME changed from "Jan" to "User" in config.py
  - [x] No hardcoded personal paths
  - [x] No credentials or API keys in code
  - [x] No test data with personal information

- [x] **Version References Updated**
  - [x] README.md shows v2.0
  - [x] install.bat shows v2.0
  - [x] setup_wizard.py references v2.0
  - [x] CHANGELOG.md created with v2.0 details

- [x] **Dependencies Verified**
  - [x] requirements.txt up to date
  - [x] requirements-stable.txt present (fallback)
  - [x] All imports in Python 3.11+ compatibility
  - [x] No missing dependencies

### Phase 2: Documentation

- [x] **Essential Documentation Created**
  - [x] README.md comprehensive and user-friendly
  - [x] CHANGELOG.md with full version history
  - [x] QUICK_START_GUIDE.md for 5-minute setup
  - [x] LICENSE file present (verify content)

- [ ] **Documentation Accuracy**
  - [ ] Installation steps tested
  - [ ] Troubleshooting steps verified
  - [ ] System requirements accurate
  - [ ] Feature list complete

### Phase 3: Setup Experience

- [x] **Setup Wizard Enhanced**
  - [x] Python version check (3.11+)
  - [x] Ollama connectivity test
  - [x] Dependency installation
  - [x] User-friendly error messages
  - [x] v2.0 features configuration

- [ ] **Installation Scripts**
  - [ ] install.bat tested on Windows
  - [ ] install.sh created for Linux/Mac
  - [ ] uninstall.bat works correctly
  - [ ] Shortcuts created properly

### Phase 4: Package Creation

- [x] **Distribution Script Created**
  - [x] create_distribution_v2.ps1 written
  - [x] Excludes development files
  - [x] Includes all essential files
  - [x] Verifies critical modules

- [ ] **Package Testing**
  - [ ] Run create_distribution_v2.ps1
  - [ ] Verify Seven-AI-v2.0-Complete.zip created
  - [ ] Extract to temp folder
  - [ ] Test installation from extracted files

### Phase 5: Functional Testing

- [ ] **Core Functionality**
  - [ ] Seven launches without errors
  - [ ] Voice input/output works
  - [ ] GUI displays correctly
  - [ ] Tray icon appears and functions

- [ ] **v2.0 Systems**
  - [ ] V2.0 modules import successfully
  - [ ] Emotional memory initializes
  - [ ] Relationship tracking works
  - [ ] Learning system active
  - [ ] Proactive engine functions
  - [ ] Goal system operational

- [ ] **Basic Conversation**
  - [ ] Seven responds to greetings
  - [ ] Seven remembers conversation context
  - [ ] Emotions display in GUI
  - [ ] No critical errors in logs

### Phase 6: Quality Assurance

- [ ] **Code Quality**
  - [ ] No debug print statements in production
  - [ ] No test files in distribution
  - [ ] No TODO comments for critical issues
  - [ ] Clean console output (minimal warnings)

- [ ] **Security Check**
  - [ ] No exposed credentials
  - [ ] No dangerous default settings
  - [ ] File permissions appropriate
  - [ ] Network access properly scoped

- [ ] **Performance Check**
  - [ ] Startup time < 10 seconds
  - [ ] Response time < 3 seconds
  - [ ] Memory usage reasonable
  - [ ] No memory leaks during 1-hour test

### Phase 7: Documentation Verification

- [ ] **User-Facing Docs**
  - [ ] README.md grammar checked
  - [ ] QUICK_START_GUIDE.md tested step-by-step
  - [ ] CHANGELOG.md accurate
  - [ ] Screenshots/examples up to date (if any)

- [ ] **Technical Accuracy**
  - [ ] Python version requirement correct (3.11+)
  - [ ] Ollama URL correct (http://localhost:11434)
  - [ ] File paths use forward slashes or Path objects
  - [ ] All referenced files exist

---

## 🔍 VERIFICATION STEPS

### Step 1: Create Package
```powershell
cd C:\Users\USER-PC\source\Code\voice-chat\python-chat-bot\enhanced-bot
.\create_distribution_v2.ps1
```

Expected output: `Seven-AI-v2.0-Complete.zip` (~5-10 MB)

### Step 2: Clean Test Environment
```powershell
# Extract to fresh directory
mkdir C:\Temp\Seven-Test
cd C:\Temp\Seven-Test
Expand-Archive Seven-AI-v2.0-Complete.zip
cd Seven-AI-v2.0-Complete
```

### Step 3: Test Installation
```powershell
# Run installer
.\install.bat

# Follow setup wizard
# Answer questions as first-time user
```

### Step 4: Test Launch
```powershell
# Launch Seven
python main_with_gui_and_tray.py

# Verify:
# - GUI appears
# - No console errors
# - Seven greets you
# - Voice works
```

### Step 5: Test v2.0 Systems
```python
# In Python console:
from core.v2 import seven_v2_complete
from core.v2 import emotional_memory
from core.v2 import relationship_model
from core.v2 import learning_system
from core.v2 import proactive_engine
from core.v2 import goal_system
from core.v2 import advanced_capabilities

# All should import successfully
print("v2.0 OK!")
```

### Step 6: Conversation Test
Have a brief conversation:
1. Greet Seven
2. Ask a question
3. Give feedback ("be more concise")
4. Check GUI for emotions and relationship
5. Wait 5 minutes for proactive behavior

### Step 7: Log Review
```powershell
# Check for errors
type %USERPROFILE%\.chatbot\bot.log
```

Should see:
- ✅ v2.0 systems initialized
- ✅ Ollama connection successful
- ✅ No critical errors
- ⚠️ Minor warnings acceptable

---

## ⚠️ KNOWN ISSUES (ACCEPTABLE)

These issues are present but non-blocking:

1. **Unicode Encoding Warnings** (Cosmetic)
   - Console may show encoding warnings
   - Does not affect functionality
   - User won't notice

2. **PyAudio Installation** (Optional)
   - May fail on some systems
   - Seven works without it
   - Setup wizard handles gracefully

3. **Vision System** (Disabled by Default)
   - Requires OpenCV
   - Not critical for core functionality
   - Can be enabled by user later

---

## 🚨 BLOCKING ISSUES

These MUST be resolved before release:

1. **Ollama Not Running**
   - Seven cannot function without Ollama
   - Setup wizard must check and warn
   - Documentation must be clear

2. **Python < 3.11**
   - v2.0 may have compatibility issues
   - Setup wizard must check version
   - Clear error message required

3. **Critical Module Import Failures**
   - If any v2.0 module fails to import
   - Seven cannot achieve 98/100 sentience
   - Must be tested and fixed

---

## 📊 RELEASE CRITERIA

### MUST HAVE (Blocking)
- ✅ Personal data removed
- ✅ Documentation complete
- ✅ Setup wizard functional
- ✅ Distribution package created
- [ ] Clean installation tested
- [ ] v2.0 systems verified working
- [ ] No critical bugs

### NICE TO HAVE (Non-blocking)
- [ ] Video tutorial/demo
- [ ] Website updated
- [ ] Social media announcement
- [ ] User testimonials
- [ ] FAQ section

### CAN WAIT (Post-release)
- Better error messages
- More configuration options
- Advanced troubleshooting guide
- Community forum
- Bug tracking system

---

## ✅ SIGN-OFF

Before release, complete this section:

**Date**: ______________

**Tested By**: ______________

**Test Environment**:
- OS: Windows ___ / Linux ___ / Mac ___
- Python Version: ______________
- Ollama Version: ______________

**Test Results**:
- [ ] Installation: PASS / FAIL
- [ ] First Launch: PASS / FAIL
- [ ] v2.0 Systems: PASS / FAIL
- [ ] Basic Conversation: PASS / FAIL
- [ ] GUI Display: PASS / FAIL
- [ ] No Critical Errors: PASS / FAIL

**Issues Found**:
- Critical: ______ (Must fix before release)
- High: ______ (Should fix before release)
- Medium: ______ (Can fix in v2.0.1)
- Low: ______ (Can fix in v2.1.0)

**Go/No-Go Decision**: GO / NO-GO

**Release Approved By**: ______________

**Date**: ______________

---

## 📝 NOTES

[Space for additional notes, observations, or recommendations]

---

**Checklist Version**: 1.0  
**Last Updated**: 2026-02-05  
**For**: Seven AI v2.0.0 Release
