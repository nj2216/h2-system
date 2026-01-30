# Medical Equipment Issue & Rental Management Feature

## Overview

The Medical Equipment Issue & Rental Management system enables comprehensive tracking and management of non-consumable medical items (crepe bands, hot packs, ice packs, support devices, etc.) in the H2 System.

## Key Features

### 1. **Equipment Inventory Management**
- Track non-consumable medical items with stock levels
- Monitor equipment condition (available, issued, damaged, lost)
- Set daily penalty rates for overdue equipment
- Store equipment details (code, category, cost, location)

### 2. **Issue & Return Workflow**
- Issue equipment to students with mandatory expected return dates
- Process equipment returns with condition verification
- Track issued quantity and status
- Automatic stock updates

### 3. **Overdue & Penalty Tracking**
- Automatic detection of overdue equipment
- Calculate penalties based on:
  - Days overdue × Daily penalty rate
  - Damage condition (50% of unit cost)
  - Lost items (100% replacement cost)
- Generate comprehensive penalty reports
- Track penalty payment status

### 4. **Role-Based Access Control**

#### H2 Officer
- ✓ Manage equipment inventory (add, edit, delete)
- ✓ Issue equipment to students
- ✓ Process returns and verify condition
- ✓ View all equipment issues
- ✓ Access penalty reports

#### Doctor
- ✓ Issue equipment to students
- ✓ Process returns and verify condition
- ✓ View equipment issues they issued

#### Warden
- ✓ View all equipment issues
- ✓ Flag overdue items
- ✓ Monitor equipment status

#### Office Staff
- ✓ View penalty reports
- ✓ Mark penalties as paid
- ✓ Generate penalty analytics

#### Student
- ✓ View own issued equipment
- ✓ Track return dates
- ✓ View penalties due

#### Director
- ✓ Full access to all equipment features
- ✓ View inventory and reports
- ✓ Manage penalties

## Database Schema

### MedicalEquipment Model
```python
class MedicalEquipment(db.Model):
    id                  - Primary key
    name               - Equipment name (e.g., "Crepe Band 5cm")
    equipment_code     - Unique identifier (e.g., "CB-5CM")
    category           - Category (Support, Thermal, Device)
    description        - Detailed description
    quantity_available - Number available for issue
    quantity_issued    - Number currently issued
    quantity_damaged   - Number damaged during use
    quantity_lost      - Number lost
    unit_cost          - Cost per unit (for penalties)
    location           - Storage location
    daily_penalty      - Penalty per day if not returned on time
    created_at/updated_at - Timestamps
```

### EquipmentIssue Model
```python
class EquipmentIssue(db.Model):
    id                    - Primary key
    equipment_id          - FK to MedicalEquipment
    student_id            - FK to Student
    issued_by_id          - FK to User (H2/Doctor who issued)
    verified_by_id        - FK to User (H2 who verified return)
    quantity              - Quantity issued
    issued_date           - When issued
    expected_return_date  - When it should be returned
    actual_return_date    - When actually returned
    return_condition      - 'normal', 'damaged', 'lost'
    return_notes          - Notes on return
    is_overdue            - Boolean flag
    days_overdue          - Number of days overdue
    penalty_amount        - Calculated penalty in rupees
    penalty_paid          - Payment status
    penalty_paid_date     - When penalty was paid
    status                - 'Issued', 'Overdue', 'Returned', 'Defaulted'
    created_at/updated_at - Timestamps
```

## Routes & Endpoints

### Equipment Management
- `GET/POST /equipment/manage` - Add/Edit/Delete equipment (H2 only)
- `GET /equipment/inventory` - View equipment inventory (All authenticated users)
- `GET /equipment/issues` - List equipment issues (Role-based access)
- `GET/POST /equipment/issue` - Issue equipment (H2/Doctor)
- `GET/POST /equipment/return/<id>` - Process return (H2/Doctor)
- `GET /equipment/penalty-report` - View penalty reports (Office/H2)
- `POST /equipment/mark-penalty-paid/<id>` - Mark penalty paid (Office/H2)
- `GET /equipment/student-dashboard` - Student view of their equipment

## Penalty Calculation

### Overdue Penalty
```
Overdue Penalty = Days Overdue × Daily Penalty Rate × Quantity
```

### Damage Penalty
```
Damage Penalty = Unit Cost × 0.5 × Quantity
```

### Loss Penalty
```
Loss Penalty = Unit Cost × Quantity
```

### Total Penalty
```
Total = Overdue Penalty + Condition Penalty
```

## Workflow Example

### Issue Equipment
1. H2/Doctor selects student and equipment
2. Sets expected return date (e.g., 7 days)
3. System creates EquipmentIssue record
4. Equipment quantity_available decreases
5. Equipment quantity_issued increases

### Track Overdue
- System periodically checks for overdue issues
- Marks as overdue if expected_return_date < current_date
- Calculates days_overdue
- Computes penalty_amount

### Process Return
1. H2/Doctor selects return condition (normal/damaged/lost)
2. Adds return notes if needed
3. System calculates penalties if applicable:
   - Days overdue penalty
   - Condition-based penalty
4. Updates equipment quantities:
   - Decreases quantity_issued
   - Increases quantity_available (if normal)
   - Increases quantity_damaged (if damaged)
   - Increases quantity_lost (if lost)
5. Sets status to 'Returned'

## Sample Equipment Data

The system comes with pre-loaded equipment:

### Support Equipment
- Crepe Bandages (5cm, 10cm) - ₹50-75, ₹5-7.50/day penalty
- Knee/Elbow/Ankle Support Braces - ₹200-300, ₹12-20/day penalty
- Back Support Belt - ₹400, ₹20/day penalty
- Neck Collar - ₹350, ₹15/day penalty

### Thermal Equipment
- Hot Pack (Electric) - ₹500, ₹25/day penalty
- Ice Pack Gel - ₹150, ₹10/day penalty

### Medical Devices
- TENS Machine - ₹2000, ₹100/day penalty
- Digital Thermometer - ₹300, ₹15/day penalty
- Blood Pressure Monitor - ₹1500, ₹75/day penalty

## Navigation Integration

### Role-Based Menu Items
- **H2 Officer**: Equipment link in navbar (Inventory & Management)
- **Doctor**: "Issue Equipment" link
- **Warden**: "Equipment" link (to view issues)
- **Office**: "Equipment Penalties" link (penalty reports)
- **Student**: "My Equipment" link (personal dashboard)
- **Director**: Full access to Equipment section

## Features Implementation

### Form Validation
- Equipment availability check before issue
- Quantity validation
- Date validation for return dates

### Dynamic UI
- Real-time available quantity updates
- Penalty calculation preview on return form
- Status-based filtering and display

### Error Handling
- Prevents issue if insufficient stock
- Validates return conditions
- Prevents deletion of equipment with active issues

## Integration with Existing System

### User Roles
- Integrated with existing RBAC system
- Uses current_user for access control
- Respects user roles and permissions

### Database
- Uses existing SQLAlchemy setup
- Follows existing model patterns
- Integrates with app initialization

### Navigation
- Added to base.html navbar
- Role-specific menu items
- Consistent styling with existing UI

## API Response Format

### Equipment List
```json
{
    "equipment": [
        {
            "id": 1,
            "name": "Crepe Band 5cm",
            "code": "CB-5CM",
            "available": 20,
            "issued": 5,
            "damaged": 1,
            "lost": 0
        }
    ]
}
```

### Issue Details
```json
{
    "id": 1,
    "student": "John Doe (123456)",
    "equipment": "Crepe Band 5cm",
    "issued_date": "2024-01-15",
    "expected_return": "2024-01-22",
    "status": "Issued",
    "penalty": 0.00
}
```

## Reports & Analytics

### Penalty Report Features
- Filter by paid/unpaid status
- Search by student or equipment
- Pagination for large result sets
- Total outstanding penalties summary
- Payment date tracking

### Inventory Report
- Stock levels by category
- Damaged/Lost items tracking
- Equipment utilization metrics
- Location-based inventory

## Future Enhancements

1. **Bulk Return Processing**: Process multiple returns at once
2. **Equipment Maintenance Logs**: Track maintenance history
3. **Damage Report Photos**: Attach images to damage reports
4. **Return Reminders**: Auto-notify students of upcoming return dates
5. **Equipment Reservation**: Reserve equipment in advance
6. **Penalty Waivers**: Approve penalty waivers with justification
7. **Equipment Categories**: Expanded categorization and filtering
8. **Equipment History**: View historical usage by equipment
9. **Student Equipment Report**: Track usage patterns by student
10. **Cost Analysis**: Equipment utilization cost analysis

## Testing

### Sample Data
- Run `python run.py` to create sample equipment
- Login with any role user
- Test issue/return workflow
- Verify penalty calculations

### Manual Testing Checklist
- [ ] Issue equipment with valid quantity
- [ ] Verify stock updates correctly
- [ ] Mark equipment overdue
- [ ] Process return with condition
- [ ] Verify penalties calculated
- [ ] Check penalty reports
- [ ] Test role-based access control
- [ ] Verify pagination works
- [ ] Test search/filter functionality

## Troubleshooting

### Issue Not Appearing
- Check student exists in system
- Verify equipment stock > 0
- Check user permissions

### Penalty Not Calculated
- Verify expected_return_date < current_date
- Check daily_penalty value > 0
- Ensure condition is set on return

### Stock Not Updating
- Check database commit status
- Verify transaction completed
- Check for database locks

## Support

For issues or questions, contact the H2 System administrator.
