# Code Cleanup Report — HealthSaathi Project

**Date**: July 31, 2026  
**Total Dead/Duplicate Code Found**: ~425 lines  
**Priority**: CRITICAL (impacts maintainability and testability)

---

## 1. CRITICAL DUPLICATIONS (Must Fix)

### 1.1 Patient Lookup Query — 13 Instances, ~25 Lines

**Pattern**: `db.query(Patient).filter(Patient.id == patient_id).first()`

**Affected Endpoints**:
- `appointments.py`: 4 occurrences (lines 153, 325, 424, 561)
- `allergies.py`: 2 occurrences (lines 82, 170)
- `medical_records.py`: 2 occurrences (lines 162, 909)
- `procedures.py`: 2 occurrences (lines 76, 162)
- `vitals.py`: 3 occurrences (lines 99, 199, 229)

**Action**: Create utility function in `app/core/utils.py`
```python
def get_patient_by_id(db: Session, patient_id: int) -> Patient:
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient
```

**Savings**: ~13 lines + consistent error handling

---

### 1.2 Access Control Functions — 3 Instances, ~40 Lines

**Affected Files**:
- `allergies.py:44-63` → `_assert_read_access()`
- `procedures.py:44-58` → `_assert_read_access()`
- `vitals.py:61-79` → `_assert_patient_access()`

**Pattern**: All check if user is staff OR patient owner

**Action**: Create generic function in `app/core/utils.py`
```python
def check_patient_access(db: Session, current_user: User, patient_id: int):
    """Verify user is staff (Doctor/Nurse/Admin) or is the patient."""
    if current_user.is_staff:
        return  # Staff can access
    if current_user.id == patient_id:
        return  # Patient can access own records
    raise HTTPException(status_code=403, detail="Unauthorized")
```

**Savings**: ~40 lines + unified access control

---

### 1.3 Response Builders — 5 Instances, ~100 Lines

**Affected Files** (each has `_build_response()` function):
- `allergies.py:26-41`
- `procedures.py:26-41`
- `vitals.py:35-58`
- `organizations.py:20-31`
- `providers.py:21-32`

**Action**: Remove and use Pydantic schema `.from_orm()` directly in responses

**Before**:
```python
def _build_response(record):
    return AllergyResponse(
        id=record.id,
        name=record.name,
        ...
    )
```

**After**: Return ORM model directly; FastAPI/Pydantic auto-converts

**Savings**: ~100 lines + faster JSON serialization

---

## 2. HIGH PRIORITY DUPLICATIONS

### 2.1 Mobile Service List Parsing — 4 Services, ~45 Lines

**Affected Services**:
- `vitals_service.dart:44-50, 56-62`
- `allergy_service.dart:39-49, 55-61`
- `procedure_service.dart:9-15, 18-24`
- `medical_record_service.dart:9-15, 18-24`

**Pattern**:
```dart
final response = await _apiClient.get('/endpoint/');
final data = response as Map<String, dynamic>;
return (data['items'] as List)
    .map((json) => Model.fromJson(json as Map<String, dynamic>))
    .toList();
```

**Action**: Create generic helper in `lib/services/api_client.dart`
```dart
Future<List<T>> getList<T>(String endpoint, T Function(Map<String, dynamic>) fromJson) async {
  final response = await get(endpoint) as Map<String, dynamic>;
  return ((response['items'] ?? []) as List)
      .map((json) => fromJson(json as Map<String, dynamic>))
      .toList();
}
```

**Savings**: ~45 lines + centralized error handling

---

### 2.2 Endpoint CRUD Pattern Duplication — ~150 Lines

**Pattern**: All CRUD endpoints repeat:
- Validation logic
- Error handling (not found, unauthorized, conflict)
- Audit chain creation
- WebSocket notification

**Affected Endpoints**: `allergies`, `procedures`, `vitals` (3 × 50 lines = 150 lines)

**Action**: Create endpoint helper functions in `app/core/crud_helpers.py`
```python
async def create_record_with_audit(
    db: Session,
    model_class,
    data,
    current_user: User,
    record_type: str,
):
    """Generic CRUD create with audit logging."""
    record = model_class(**data.dict())
    db.add(record)
    db.flush()
    await create_audit_entry(db, record_type, record.id, current_user.id)
    db.commit()
    return record
```

**Savings**: ~150 lines

---

## 3. MEDIUM PRIORITY

### 3.1 Duplicate Import — 1 Line

**File**: `medical_records.py`  
**Lines**: 9 and 24

**Issue**: `UserRole` imported twice

**Action**: Remove duplicate on line 24

**Savings**: 1 line (but improves cleanliness)

---

## 4. INCOMPLETE IMPLEMENTATIONS (TODO Items)

### 4.1 Token Blacklist Not Scalable (CRITICAL)

**File**: `app/core/dependencies.py:22-24`

**Issue**:
```python
# TODO: replace with Redis (or another shared store) in production
BLACKLISTED_TOKENS = set()  # In-memory, lost on restart, not shared across workers
```

**Status**: Works for single-server dev; fails at scale

**Action**: Document as deployment note OR upgrade to Redis if multi-process needed

**Priority**: Document for capstone (don't implement unless required for deployment)

---

### 4.2 Android Release Build Config Not Specified

**File**: `project/mobile/android/app/build.gradle.kts`  
**Lines**: 23, 35

**Issue**: Application ID and signing config not set

**Status**: App won't build for Google Play Store

**Action**: Either:
1. Set dummy values for development
2. Document that release build requires manual signing config
3. Create GitHub Actions secret for CI/CD signing

**Priority**: LOW (dev/testing doesn't need this)

---

## 5. CLEANUP EXECUTION PLAN

### Phase 1: Backend Utilities (2 hours)
1. Create `app/core/utils.py`
2. Add `get_patient_by_id()`
3. Add `check_patient_access()`
4. Update all 13 endpoints to use these

### Phase 2: Response Builders (1 hour)
1. Remove `_build_response()` from 5 endpoint files
2. Use Pydantic `.from_orm()` directly
3. Test JSON serialization

### Phase 3: CRUD Helpers (1.5 hours)
1. Create `app/core/crud_helpers.py`
2. Extract common patterns
3. Update `allergies`, `procedures`, `vitals` endpoints
4. Run tests to verify

### Phase 4: Mobile Services (1 hour)
1. Add `getList<T>()` helper to `api_client.dart`
2. Update 4 services to use it
3. Run `flutter analyze`

### Phase 5: Import Cleanup (0.25 hours)
1. Remove duplicate import in `medical_records.py`
2. Run linter

### Phase 6: Verification (1 hour)
1. Run full test suite
2. Run `flutter analyze`
3. Verify no regressions

**Total Time**: ~6-7 hours  
**Risk Level**: LOW (refactoring, no logic changes)  
**Rollback**: Easy (git revert if needed)

---

## 6. CODE QUALITY METRICS

**Before Cleanup**:
- Total lines (backend + mobile): ~22,600
- Duplicate code: ~425 lines
- Duplication ratio: 1.9%

**After Cleanup**:
- Total lines (backend + mobile): ~22,175 (estimated)
- Duplicate code: <50 lines (unavoidable, inherent patterns)
- Duplication ratio: <0.2%

**Quality Gain**: ~2.2% reduction in code duplication

---

## 7. Files to Modify/Create

### Create (New Files)
- ✅ `app/core/utils.py` (40-60 lines)
- ✅ `app/core/crud_helpers.py` (50-80 lines)

### Modify (Backend Endpoints)
- ✅ `app/api/v1/endpoints/appointments.py` (4 line deletions)
- ✅ `app/api/v1/endpoints/allergies.py` (60 line deletions + refactor)
- ✅ `app/api/v1/endpoints/medical_records.py` (63 line deletions + 1 duplicate import)
- ✅ `app/api/v1/endpoints/procedures.py` (50 line deletions + refactor)
- ✅ `app/api/v1/endpoints/vitals.py` (78 line deletions + refactor)
- ✅ `app/api/v1/endpoints/organizations.py` (30 line deletions)
- ✅ `app/api/v1/endpoints/providers.py` (30 line deletions)

### Modify (Mobile Services)
- ✅ `lib/services/api_client.dart` (add generic helper)
- ✅ `lib/services/vitals_service.dart` (refactor 2 methods)
- ✅ `lib/services/allergy_service.dart` (refactor 2 methods)
- ✅ `lib/services/procedure_service.dart` (refactor 2 methods)
- ✅ `lib/services/medical_record_service.dart` (refactor 2 methods)

---

## 8. NEXT STEPS

**User Action Required**: Approve cleanup execution

Options:
1. **Full Cleanup**: Execute all phases 1-6 (6-7 hours, no risk)
2. **Priority Cleanup**: Execute phases 1-3 only (4 hours, highest impact)
3. **Custom**: Specify which duplications to fix first

**Recommendation**: Start with **Phase 1** (backend utils) — highest impact with lowest risk.

---

## References

- Agent analysis output: `a1aeb530d8d8c3396`
- Resource efficiency benchmark: `SESSION_WORK_LOG_2026_07_30_31.md`
- CLAUDE.md rules: Never invent, verify against code, keep it clean
