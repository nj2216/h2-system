# Equipment Management - Deployment & Configuration Guide

## Installation

### Prerequisites
- Flask application running
- SQLAlchemy ORM configured
- Bootstrap 5.3+ for UI
- Python 3.7+

### Step 1: Database Initialization

Run the application to create tables:
```bash
python run.py
```

This automatically:
- Creates `medical_equipments` table
- Creates `equipment_issues` table
- Loads 12 sample equipment items
- Indexes equipment_code as unique

### Step 2: Verify Installation

Check that these files exist:
```
✓ app/equipment/__init__.py
✓ app/equipment/routes.py
✓ app/models.py (updated with new models)
✓ app/__init__.py (updated with blueprint)
✓ app/templates/base.html (updated with menu)
✓ app/templates/equipment/*.html (7 templates)
```

### Step 3: Access the Feature

Navigate to:
- H2 Staff: `/equipment/inventory`
- Issue Equipment: `/equipment/issue`
- View Issues: `/equipment/issues`
- Penalties: `/equipment/penalty-report`
- Student: `/equipment/student-dashboard`

## Configuration

### Daily Penalty Rates

Adjust penalty rates per equipment based on value:

| Equipment Type | Daily Penalty | Example |
|---|---|---|
| Low Value (₹50-100) | ₹5-10 | Bandages |
| Medium Value (₹200-500) | ₹10-25 | Support Braces |
| High Value (₹1000+) | ₹50-100 | Devices |

### Equipment Categories

Current categories in sample data:
- **Support** - Bandages, braces, collars
- **Thermal** - Hot/Ice packs
- **Device** - Electronic equipment
- **Other** - Custom additions

Add more via Manage Equipment form.

### Return Date Defaults

Current default: 7 days

To change, modify in `issue.html`:
```html
<input type="number" value="7" /> <!-- Change to desired days -->
```

## API Configuration

### Request/Response Examples

#### Issue Equipment
```bash
POST /equipment/issue
Content-Type: application/x-www-form-urlencoded

student_id=1
equipment_id=5
quantity=1
expected_return_days=7
```

#### Process Return
```bash
POST /equipment/return/1
Content-Type: application/x-www-form-urlencoded

condition=normal
notes=Equipment in good condition
```

#### Mark Penalty Paid
```bash
POST /equipment/mark-penalty-paid/1
```

## Database Maintenance

### Backup & Restore

#### Backup Equipment Data
```bash
sqlite3 h2_system.db ".tables"  # Verify tables exist
sqlite3 h2_system.db ".dump medical_equipments equipment_issues" > backup.sql
```

#### Restore
```bash
sqlite3 h2_system.db < backup.sql
```

### Common Queries

#### Check Equipment Stock
```sql
SELECT name, quantity_available, quantity_issued, quantity_damaged 
FROM medical_equipments;
```

#### View Unpaid Penalties
```sql
SELECT 
    ei.id,
    s.roll_number,
    me.name,
    ei.penalty_amount
FROM equipment_issues ei
JOIN students s ON ei.student_id = s.id
JOIN medical_equipments me ON ei.equipment_id = me.id
WHERE ei.penalty_paid = 0;
```

#### Find Overdue Items
```sql
SELECT 
    ei.id,
    s.roll_number,
    me.name,
    ei.expected_return_date,
    julianday('now') - julianday(ei.expected_return_date) as days_overdue
FROM equipment_issues ei
JOIN students s ON ei.student_id = s.id
JOIN medical_equipments me ON ei.equipment_id = me.id
WHERE ei.actual_return_date IS NULL
AND ei.expected_return_date < datetime('now');
```

## Performance Optimization

### Indexing

The following are automatically indexed:
- MedicalEquipment.equipment_code (UNIQUE)
- EquipmentIssue.student_id (FK)
- EquipmentIssue.equipment_id (FK)

For high-volume deployments, consider:
```sql
CREATE INDEX idx_equipment_issue_status ON equipment_issues(status);
CREATE INDEX idx_equipment_issue_issued_date ON equipment_issues(issued_date);
CREATE INDEX idx_equipment_issue_penalty ON equipment_issues(penalty_paid);
```

### Query Optimization

The system uses:
- Pagination (20 items per page)
- Selective column loading
- Relationship eager loading where needed

## Security Considerations

### Access Control
- All routes protected with login_required
- Role-based access via @require_role decorator
- Student can only view own equipment

### Input Validation
- Equipment availability checked before issue
- Quantity validation (positive integers only)
- Date validation (return date > today)
- Condition enum validation (normal/damaged/lost)

### SQL Injection Prevention
- SQLAlchemy ORM used for all queries
- Parameterized queries by default
- No raw SQL execution

### CSRF Protection
- Flask-WTF integration ready
- Add to forms if needed: `{{ csrf_token() }}`

## Error Handling

### Common Errors & Solutions

#### "Insufficient stock" error
```
Cause: Equipment quantity_available < requested quantity
Fix: Reduce quantity or select different equipment
```

#### "Insufficient permissions" error
```
Cause: User role not authorized for endpoint
Fix: Verify user has correct role assigned
```

#### "Equipment not found" error
```
Cause: Invalid equipment_id in URL
Fix: Verify equipment ID from inventory list
```

#### Database locked error
```
Cause: Concurrent write operations
Fix: Retry request, increase timeout, or reduce concurrent users
```

## Monitoring & Logging

### Key Metrics to Monitor

1. **Stock Health**
   - Equipment availability vs. issued ratio
   - Damaged/Lost percentages
   - Reorder frequency

2. **Penalty Metrics**
   - Total outstanding penalties
   - Collection rate (paid/unpaid ratio)
   - Average penalty amount
   - Overdue item count

3. **Usage Metrics**
   - Equipment utilization rate
   - Issue frequency per equipment
   - Average issue duration

### Logging Setup

For production, add logging:
```python
import logging

logger = logging.getLogger(__name__)

# In routes:
logger.info(f"Equipment issued: {equipment.name} to student {student.id}")
logger.warning(f"Equipment overdue: {issue.id} - {days_overdue} days")
logger.error(f"Stock update failed: {error}")
```

## Maintenance Tasks

### Daily
- [ ] Check for newly overdue items
- [ ] Review penalty reports
- [ ] Process penalty payments

### Weekly
- [ ] Generate equipment utilization report
- [ ] Verify stock levels
- [ ] Check for damaged items needing repairs

### Monthly
- [ ] Full inventory audit
- [ ] Reconcile penalties with records
- [ ] Archive old records (optional)
- [ ] Update equipment costs if needed

### Quarterly
- [ ] Review equipment categories
- [ ] Adjust penalty rates based on inflation
- [ ] Plan equipment replacements
- [ ] User access audit

## Scaling Considerations

### For Small Deployments (< 500 students)
- Current configuration works fine
- SQLite sufficient
- Single-user access pattern acceptable

### For Medium Deployments (500-2000 students)
- Consider PostgreSQL for concurrency
- Add database indexes for queries
- Implement caching for inventory
- Monitor response times

### For Large Deployments (> 2000 students)
- PostgreSQL with connection pooling
- Redis caching for equipment data
- Async task processing for penalties
- Database replication for backup

## Migration from Other Systems

If migrating from legacy equipment tracking:

1. **Export equipment data** to CSV format
2. **Transform to match schema**:
   ```
   name, equipment_code, category, unit_cost, daily_penalty, location
   ```
3. **Load via bulk insert**:
   ```python
   for row in csv_data:
       equipment = MedicalEquipment(**row)
       db.session.add(equipment)
   db.session.commit()
   ```
4. **Validate data** in inventory view
5. **Migrate historical issues** if needed

## Backup & Disaster Recovery

### Daily Backups
```bash
# Automated backup script
sqlite3 h2_system.db ".backup h2_system_backup.db"
# Upload backup_$(date +%Y%m%d).db to cloud storage
```

### Recovery Procedures
1. Stop the application
2. Restore database from backup
3. Verify data integrity
4. Restart application
5. Test core functionality

## Support & Troubleshooting

### Getting Help
- Check EQUIPMENT_MANAGEMENT.md for detailed docs
- Review EQUIPMENT_QUICKSTART.md for workflows
- Check error messages in application logs
- Verify database tables created: `python -c "from app.models import *; from app import create_app, db; app = create_app(); app.app_context().push(); print([t.name for t in db.inspect(db.engine).get_table_names()])"`

### Common Debugging

Check if equipment table exists:
```python
from app import create_app, db
from app.models import MedicalEquipment

app = create_app()
with app.app_context():
    count = MedicalEquipment.query.count()
    print(f"Equipment items: {count}")
```

Verify blueprint registered:
```python
from app import create_app
app = create_app()
for rule in app.url_map.iter_rules():
    if 'equipment' in rule.rule:
        print(rule)
```

## Version History

### v1.0 (January 30, 2026)
- Initial release
- Equipment inventory management
- Issue/return workflow
- Automatic penalty calculation
- Role-based access control
- Penalty tracking and reports
- Student dashboard
- 12 sample equipment items

## Contact & Support

For issues, feature requests, or support:
- System Administrator: [contact info]
- H2 System Documentation: [link]
- Code Repository: [GitHub/GitLab link]

---

**Last Updated:** January 30, 2026  
**Maintained By:** Development Team  
**Status:** Production Ready
