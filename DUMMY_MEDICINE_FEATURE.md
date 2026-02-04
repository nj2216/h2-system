# Dummy Medicine Feature Implementation

## Overview
The dummy medicine feature allows the system to gracefully handle two scenarios:
1. **Out-of-stock medicines**: Existing medicines that exist in the system but have zero available quantity
2. **New medicines**: Completely new medicines that don't exist in the database, entered by doctors on the fly

## Backend Implementation (Complete)

### Model: `DummyMedicine` (app/models.py)
- Stores placeholder medicines with fields: name, generic_name, dosage, unit, supplier, estimated_cost, notes
- Linked to real medicine via `replaced_by_id` when replacement occurs
- Tracked via `PrescriptionItem.dummy_medicine_id`

### Auto-Creation Logic (app/health/routes.py)
When creating prescriptions:
1. **For out-of-stock medicines**: Backend checks if medicine stock (`total_batch_quantity`) is sufficient for prescribed quantity
2. **For new medicines**: Doctor clicks "Add New Medicine Not in List" and provides medicine name/dosage
3. If stock is insufficient OR if new medicine is selected:
   - A `DummyMedicine` is created automatically with provided details
   - The prescription item is linked to the dummy medicine
   - Item status is set to `OUT_OF_STOCK`

### Replacement Workflow
- Route: `/health/prescription-items/<item_id>/replace-dummy` 
- Allows H2 staff to replace dummy medicine with real medicine when stock arrives
- Updates `replaced_by_id` link and item status

## Frontend Implementation (Complete)

### 1. Add New Medicine Option

**Files Updated:**
- `create_prescription.html` (lines 166-167)
- `prescribe_during_visit.html` (lines 165-167)

**Display:**
```
➕ Add New Medicine Not in List
```

When selected, opens modal form for entering new medicine details.

### 2. New Medicine Modal Form

**Fields:**
- **Medicine Name** (Required): Name of the medicine
- **Generic Name** (Optional): Generic/chemical name
- **Dosage**: e.g., "500mg", "250mg Tablets"
- **Unit** (Dropdown): Tablets, Capsules, ml, Injections, Patches, Cream, Drops

**Example:**
Doctor enters:
- Name: "Azithromycin"
- Generic: "Azithromycin"
- Dosage: "500mg Tablets"
- Unit: "Tablets"

### 3. Medicine Selection Displays Stock Status

**Changes:**
- Out-of-stock medicines show: "⚠️ Medicine Name – OUT OF STOCK"
- Available medicines show: "Medicine Name – Stock: X units"
- New medicines entered via modal are marked as "NEW MEDICINE" with purple badge

**Example:**
```
⚠️ Paracetamol (500mg) – OUT OF STOCK        [Status: OUT OF STOCK]
Ibuprofen (400mg) – Stock: 25 Tablets       [Status: OK]
Azithromycin (500mg Tablets)                [Status: NEW MEDICINE]
```

### 4. Stock Status Badge

**Dynamic Color Indicator:**
- **RED**: OUT OF STOCK (0 quantity for existing medicines)
- **ORANGE**: LOW STOCK (< 5 quantity)
- **GREEN**: OK (≥ 5 quantity)
- **PURPLE**: NEW MEDICINE (doctor-entered)

Updates in real-time when medicine selected in the form.

### 5. Form Submission Handling

**Backend Processing:**
- Collects new medicine data from modal form
- Creates `DummyMedicine` record with provided details
- Links prescription item to dummy medicine
- Sets item status to `OUT_OF_STOCK`

**Form Submission Steps:**
1. Doctor selects "Add New Medicine Not in List"
2. Modal opens automatically
3. Doctor fills in medicine details
4. Clicks "Add Medicine" button
5. Modal closes, medicine appears as "NEW MEDICINE" in row
6. Doctor continues filling prescription
7. On submit, system creates dummy medicine and prescription

### 6. Flash Messages

**Upon Prescription Creation:**
- Success message: "Prescription created with X medicine(s). Ready for dispensing."
- Info message (if new medicines): "New medicines added to prescription: Medicine1 (500mg); Medicine2. These can be replaced with real medicines once stock arrives."
- Warning message (if out-of-stock): "The following medicines are out of stock and may need to be created as dummy medicines: [list]"

### 7. Prescriptions List Display

Dummy medicines now show with ⚠️ icon in medicines column:
- Real medicine: `Paracetamol`
- Dummy medicine: `⚠️ Azithromycin (NEW)`
- Out-of-stock medicine: `⚠️ Medicine Name`

### 8. Prescription View Details

Displays alert box for each dummy medicine showing:
- "Out of Stock Placeholder" warning
- Supplier name (if available)
- Estimated cost (if available)
- Notes (if available)
- "Replace with Real Medicine" button for H2 staff

## User Workflow

### Scenario 1: Out-of-Stock Existing Medicine
1. Doctor selects medicine that exists but has 0 stock
2. Medicine shows with ⚠️ "OUT OF STOCK"
3. Badge shows "OUT OF STOCK" in red
4. On prescription creation, system auto-creates dummy medicine
5. User sees warning: "Medicine name is out of stock and may need to be created as dummy medicine"

### Scenario 2: Completely New Medicine
1. Doctor clicks "Add New Medicine Not in List"
2. Modal opens
3. Doctor enters: Name="Azithromycin", Dosage="500mg", Unit="Tablets"
4. Clicks "Add Medicine" button
5. Medicine appears in row with "NEW MEDICINE" purple badge
6. Doctor completes prescription form
7. On submit, system creates DummyMedicine record
8. User sees info message: "New medicines added to prescription: Azithromycin (500mg)"

### Scenario 3: Replace Dummy with Real Medicine
1. When real medicine stock arrives
2. H2 staff navigates to prescription view
3. Sees "Out of Stock Placeholder" alert
4. Clicks "Replace with Real Medicine"
5. Selects available real medicine
6. System updates prescription item to use real medicine
7. Item status updated accordingly

## Database Changes
- No new database fields needed
- Uses existing `PrescriptionItem.dummy_medicine_id` column
- Creates records in `DummyMedicine` table for both out-of-stock and new medicines

## Technical Details

### Form Data Structure
New medicines are stored as JSON in hidden form field:
```json
{
  "name": "Azithromycin",
  "generic_name": "Azithromycin",
  "dosage": "500mg Tablets",
  "unit": "Tablets"
}
```

### Backend Processing
```python
# Extract new medicine data from form
is_new_medicine_list = request.form.getlist('is_new_medicine[]')

# For each new medicine
medicine_data = json.loads(is_new_medicine_list[idx])
dummy_medicine = DummyMedicine(
    name=medicine_data['name'],
    generic_name=medicine_data['generic_name'],
    dosage=medicine_data['dosage'],
    unit=medicine_data['unit']
)
# Link to prescription item with status='OUT_OF_STOCK'
```

## Error Handling
- If new medicine name is empty, modal shows error: "Please enter medicine name"
- If JSON parsing fails, system shows warning with error details
- Invalid form values are caught and logged
- Graceful fallback to prevent prescription creation failure

## Future Enhancements (Optional)
1. Pre-populate generic name based on medicine name (using drug database API)
2. Add supplier/cost fields to new medicine form
3. Auto-complete medicine names based on partial input
4. Add bulk import for new medicines
5. Add notification system when new medicines are created
6. Allow admin to batch-approve new medicines into main inventory
7. Add expiry/expected arrival date for new medicines
8. Add cost tracking for new medicines added


### Model: `DummyMedicine` (app/models.py)
- Stores placeholder medicines with fields: name, generic_name, dosage, unit, supplier, estimated_cost, notes
- Linked to real medicine via `replaced_by_id` when replacement occurs
- Tracked via `PrescriptionItem.dummy_medicine_id`

### Auto-Creation Logic (app/health/routes.py)
When creating prescriptions:
1. Backend checks if medicine stock (`total_batch_quantity`) is sufficient for prescribed quantity
2. If stock is insufficient (0 available), a `DummyMedicine` is created automatically
3. The prescription item is linked to the dummy medicine instead of the real one
4. Item status is set to `OUT_OF_STOCK`

### Replacement Workflow
- Route: `/health/prescription-items/<item_id>/replace-dummy` 
- Allows H2 staff to replace dummy medicine with real medicine when stock arrives
- Updates `replaced_by_id` link and item status

## Frontend Enhancements (Recently Added)

### 1. Medicine Selection Displays Stock Status

**Files Updated:**
- `create_prescription.html` (lines 161-189)
- `prescribe_during_visit.html` (lines 165-199)

**Changes:**
- Medicine selector now shows "⚠️ OUT OF STOCK" for medicines with 0 available quantity
- Shows "Stock: X units" for available medicines
- Added informational note: "⚠️ Out-of-stock medicines will be created as dummy medicines for later replacement."

**Example:**
```
⚠️ Paracetamol (500mg) – OUT OF STOCK
Ibuprofen (400mg) – Stock: 25 Tablets
```

### 2. Stock Status Badge

**Files Updated:**
- `create_prescription.html` (lines 176-182, lines 285-305)
- `prescribe_during_visit.html` (lines 181-187, lines 277-330)

**Changes:**
- Added colored badge next to stock quantity showing status:
  - **OUT OF STOCK** (Red): Stock = 0
  - **LOW STOCK** (Orange): Stock < 5
  - **OK** (Green): Stock ≥ 5

**JavaScript Updates:**
- `updateMedicineDetails()` function now updates badge color and text dynamically
- Badge colors update when medicine is selected in the form

### 3. Out-of-Stock Warning on Form Submission

**Files Updated:**
- `app/health/routes.py` (lines 289-332)

**Changes:**
- When prescription is created, backend checks each medicine for insufficient stock
- Collects list of out-of-stock items: `[{ medicine.name (need: X, available: Y), ... }]`
- After successful prescription creation, displays warning message:
  ```
  ⚠️ WARNING: The following medicines are out of stock and may need to be created 
  as dummy medicines: Paracetamol (need: 10, available: 0); Aspirin (need: 5, available: 2)
  ```

### 4. Dummy Medicine Indicator in Prescriptions List

**Files Updated:**
- `prescriptions_list.html` (lines 73-85)

**Changes:**
- Medicines column now shows warning icon (⚠️) for dummy medicines
- Display format:
  - Real medicine: `Paracetamol`
  - Dummy medicine: `⚠️ Paracetamol (Placeholder)`

### 5. Dummy Medicine Details in Prescription View

**Files Updated:**
- `view_prescription.html` (lines 150-156, lines 182-201)

**Changes:**
- Fixed status badge colors to use proper Bootstrap classes (was showing invalid `bg-pending`, etc.)
- Displays alert box for each dummy medicine:
  - Shows "Out of Stock Placeholder" warning
  - Displays supplier name if available
  - Shows estimated cost if available
  - Shows notes if available
  - Provides "Replace with Real Medicine" button for H2 staff

**Example Display:**
```
⚠️ Out of Stock Placeholder
This medicine was not in stock when prescribed. A placeholder was created.
Supplier: ABC Pharma
Estimated Cost: ₹150
Notes: Expected delivery on 2024-01-15

[Replace with Real Medicine] button
```

## User Workflow

### 1. Doctor/H2 Staff Creates Prescription
1. Opens "Create Prescription" or "Prescribe During Visit"
2. Selects medicines from list
3. Sees out-of-stock items marked with ⚠️
4. Proceeds with prescription (backend auto-creates dummy for out-of-stock items)
5. Receives warning message showing which medicines were out of stock

### 2. H2 Staff Replaces Dummy Medicine
1. Navigates to prescription view
2. Sees "Out of Stock Placeholder" alert for dummy medicines
3. Clicks "Replace with Real Medicine" button
4. Selects available real medicine from dropdown
5. System updates prescription item to use real medicine

### 3. Pharmacist Dispenses
1. Views prescription in dispensing interface
2. Sees indicator if any medicines are dummy/out-of-stock
3. Can dispense available quantities or wait for replacement

## Database Changes
- No new database fields needed (dummy medicine relationship already exists in `PrescriptionItem` model)
- Uses existing `PrescriptionItem.dummy_medicine_id` column

## Error Handling
- If selected medicine has 0 stock, system automatically creates dummy with same details
- Status is set to `OUT_OF_STOCK` to indicate issue
- Can be replaced via "Replace with Real Medicine" workflow

## Future Enhancements (Optional)
1. Add "Quick Replace" button in prescriptions list
2. Add bulk replace for multiple dummy medicines
3. Add notification system when dummy medicines are created
4. Add admin dashboard for tracking dummy medicines
5. Add expiry notification for replacement workflow
6. Allow manual creation of dummy medicines by users (currently only automatic)
