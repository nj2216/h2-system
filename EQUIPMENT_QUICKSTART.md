# Equipment Management - Quick Start Guide

## Getting Started

### 1. Initialize the System
```bash
python run.py
```
This will:
- Create database tables
- Add default users
- Load sample equipment data

### 2. Login Credentials
Use these credentials to access the system:

| Role | Username | Password |
|------|----------|----------|
| H2 Officer | h2 | h2 |
| Doctor | doctor | doctor |
| Warden | warden | warden |
| Office | office | office |
| Director | director | director |

### 3. Common Tasks

#### As H2 Officer

**View Equipment Inventory**
1. Click "Equipment" in navbar
2. See all equipment with stock levels

**Add New Equipment**
1. Click "Equipment" → "Manage"
2. Click "Add Equipment"
3. Fill in details:
   - Equipment Name
   - Equipment Code (unique)
   - Category
   - Unit Cost
   - Daily Penalty Rate
4. Click "Add Equipment"

**Issue Equipment to Student**
1. Click "Equipment" → "Issue Equipment" (or "New Issue")
2. Select student from dropdown
3. Select equipment (only shows available items)
4. Enter quantity needed
5. Set return days (e.g., 7 days)
6. Click "Issue Equipment"

**Process Equipment Return**
1. Click "Equipment" → "Equipment Issues"
2. Click action button for the issued item
3. Select equipment condition:
   - Normal (no penalty)
   - Damaged (50% of unit cost)
   - Lost (100% replacement cost)
4. Add notes if needed
5. System shows penalty breakdown
6. Click "Confirm Return"

**View Penalty Reports**
1. Click "Equipment" → "Manage" (as H2)
2. Or Office staff can view from navbar
3. See all penalties by status
4. Mark as paid when collected

#### As Doctor

**Issue Equipment**
1. Click "Issue Equipment" in navbar
2. Follow same process as H2
3. You can verify returns you issued

**View Your Issues**
1. Go to Equipment Issues
2. See only equipment you issued
3. Process returns and verify condition

#### As Warden

**View Equipment Issues**
1. Click "Equipment" in navbar
2. See all student issues
3. Monitor overdue items

#### As Office Staff

**View Penalty Reports**
1. Click "Equipment Penalties" in navbar
2. See all outstanding penalties
3. Filter by paid/unpaid
4. Mark payments when collected

#### As Student

**Track Your Equipment**
1. Click "My Equipment" in navbar
2. See "Currently Issued" section
3. Check expected return dates
4. See penalties due (if any)
5. View "Returned Equipment" history

## Key Metrics to Monitor

### Stock Health
- ✓ Equipment in "Available" should be > 0
- ✓ Monitor "Damaged" and "Lost" items
- ✓ Reorder when availability is low

### Overdue Tracking
- ✓ Equipment Issues status shows "Overdue" if past return date
- ✓ Days overdue is calculated automatically
- ✓ Penalties accumulate daily

### Revenue Management
- ✓ Track total unpaid penalties
- ✓ Monitor penalty collection rates
- ✓ Follow up on defaulted items

## Common Workflows

### Workflow 1: Simple Equipment Issue
```
1. Student visits H2 office
2. H2 selects student and equipment (e.g., Knee Support)
3. Sets return date (e.g., 7 days)
4. Student takes equipment
5. Student returns within 7 days
6. H2 verifies condition (Normal)
7. Equipment returned to stock
```

### Workflow 2: Late Return with Penalty
```
1. Equipment issued on Jan 15
2. Expected return Jan 22
3. Student returns on Jan 25 (3 days late)
4. Equipment condition: Normal
5. Penalty = 3 days × ₹20/day = ₹60
6. Office staff collects ₹60
7. Marks penalty as paid
```

### Workflow 3: Damaged Equipment
```
1. Equipment issued: Hot Pack (₹500)
2. Student returns damaged
3. H2 selects condition: Damaged
4. Penalty = ₹500 × 50% = ₹250
5. Office processes penalty payment
6. Equipment noted as damaged for future reference
```

### Workflow 4: Lost Equipment
```
1. Equipment issued: TENS Machine (₹2000)
2. Student cannot return it
3. H2 selects condition: Lost
4. Penalty = ₹2000 (full replacement cost)
5. Office generates invoice for ₹2000
6. Student settles payment via office
```

## Frequently Asked Questions

### Q: What if equipment isn't available?
**A:** The issue form only shows equipment with quantity_available > 0. Request more stock if needed.

### Q: Can I cancel an issue?
**A:** No, but you can process an immediate return by marking condition as "Lost" if student cannot use.

### Q: How are penalties calculated?
**A:** 
- Overdue: Days × Daily Rate × Quantity
- Damaged: Unit Cost × 50% × Quantity
- Lost: Unit Cost × 100% × Quantity

### Q: Can I modify daily penalty rates?
**A:** Yes, edit equipment details in Manage Equipment section.

### Q: Can students see their penalties?
**A:** Yes, on the "My Equipment" dashboard they can see total penalties due.

### Q: How do I report equipment as lost?
**A:** Process the return and select "Lost" as condition. This triggers full replacement cost penalty.

### Q: Can I undo a return?
**A:** No, returns are permanent. Plan carefully before confirming.

### Q: How often should I check for overdue equipment?
**A:** The system checks automatically. Review Equipment Issues regularly for "Overdue" status items.

## Best Practices

### Stock Management
- ✓ Keep at least 2-3 units of popular items
- ✓ Order replacements when stock hits 25% of capacity
- ✓ Regular inventory checks monthly

### Penalty Collection
- ✓ Inform students of penalties immediately
- ✓ Offer payment plan options for large penalties
- ✓ Follow up after 7 days if unpaid
- ✓ Escalate after 30 days

### Equipment Maintenance
- ✓ Inspect equipment on return
- ✓ Document damage immediately
- ✓ Store equipment properly in designated locations
- ✓ Schedule repairs for damaged items

### Student Communication
- ✓ Provide return date reminder at issue time
- ✓ Send SMS/email reminder 2 days before return
- ✓ Clearly communicate damage policy
- ✓ Keep documentation of all issues

## Troubleshooting

### Issue "Insufficient stock" error
- **Cause:** Equipment quantity_available = 0
- **Solution:** Add more equipment or wait for pending returns

### Penalty not showing
- **Cause:** expected_return_date > today
- **Solution:** Equipment marked as overdue only after return date passes

### Can't delete equipment
- **Cause:** Equipment has active (unreturned) issues
- **Solution:** Close all issues before deletion

### Stock numbers seem wrong
- **Cause:** Incomplete return processing
- **Solution:** Check for "Issued" status items that weren't returned

## Contact & Support

For technical issues or feature requests, contact the system administrator.

---

**Last Updated:** January 2026  
**Version:** 1.0
