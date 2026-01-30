# Quick Start Guide - H2 System

## Getting Started in 5 Minutes

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the Application
```bash
python run.py
```

### 3. Login
- Open: http://localhost:5000
- **Username**: admin
- **Password**: admin

---

## Default User Roles

After login as admin, you can register other users with different roles:

| Role | Responsibilities |
|------|-----------------|
| **H2** | Health Team - Manages doctor visits, prescriptions, medical stock |
| **Warden** | Hostel Management - Manages students, assets, maintenance |
| **Office** | Admin Operations - Approves sick leave requests |
| **Director** | System Admin - User management, reports, approvals |
| **Doctor** | Medical Staff - Records visits, prescriptions |
| **Student** | Hostel Resident - Accesses personal health records |

---

## Main Features

### 1. Student Management
- **Navigation**: Students → Register Student
- Register students with personal and medical information
- Track emergency contacts
- View student profiles

### 2. Health Management
- **Navigation**: Dashboard → Health (varies by role)
- Record doctor visits
- Create prescriptions
- Track medication dispensing
- View health history

### 3. Medicine Inventory
- **Navigation**: Stock → Medicine Inventory
- Add medicines to inventory
- Track stock levels
- Set minimum stock alerts
- Record stock movements

### 4. Asset Management  
- **Navigation**: Assets → Asset List
- Register hostel assets
- Track asset location and condition
- Record maintenance history
- Generate condition reports

### 5. Sick Leave Workflow
- **Navigation**: Sick Leave → New Request
- Create sick leave/food requests
- Multi-step approval process:
  1. H2 Review
  2. Warden Verification
  3. Office Approval
  4. Director Review (optional)

### 6. Medical Equipment Management
- **Navigation**: Equipment → Issue Equipment / View Issues
- Issue equipment to students with expected return dates
- Track equipment status (Issued, Overdue, Returned)
- Process returns and verify equipment condition
- Calculate penalties for overdue, damaged, or lost items
- View penalty reports and collect payments

### 7. Role-Based Dashboards
- Each role has a customized dashboard
- View statistics and pending items
- Quick access to important functions

---

## Common Tasks

### Register a New Staff Member
1. Go to Users → Register User (Director only)
2. Fill in details and select role
3. Set password
4. Click Register User

### Create a Student Profile
1. Go to Students → Register Student
2. Fill in user account and student details
3. Add emergency contact information
4. Click Register Student

### Record a Doctor Visit
1. Go to Health → Doctor Visits
2. Click "Record Visit"
3. Select student
4. Enter diagnosis and treatment
5. Optionally add prescriptions
6. Save

### Approve a Sick Leave Request
1. Go to Sick Leave → Pending (based on your role)
2. Click on the request
3. Review details
4. Add notes (optional)
5. Click Approve or Reject
6. Request moves to next approval stage

### Check Equipment Status
1. Go to Equipment → View Issues
2. Filter by status, student, or equipment
3. Click on issue to see details
4. Process return if needed

### Issue Equipment to Student
1. Go to Equipment → Issue Equipment
2. Select student and equipment
3. Set expected return date
4. Add notes (optional)
5. Click "Issue Equipment"

### Process Equipment Return
1. Go to Equipment → View Issues
2. Find unreturned equipment
3. Click return button
4. Select condition (Normal, Damaged, Lost)
5. Add return notes
6. Confirm return (auto-calculates penalty)

### View Penalty Reports
1. Login as Office staff
2. Go to Equipment → Penalty Reports
3. Filter by status or student
4. Mark penalties as paid

### Track Your Equipment (Students)
1. Go to My Equipment
2. View currently issued equipment
3. Check return dates and overdue status
4. View returned equipment and any penalties

### Check Medicine Stock
1. Go to Stock → Medicine Inventory
2. View current stock levels
3. Click "Low Stock" for items below minimum
4. Add medicine by clicking "Add Medicine"

### Track Asset Condition
1. Go to Assets → Asset List
2. Click on an asset
3. View maintenance history
4. Add maintenance log
5. Update asset condition

---

## Tips & Tricks

✓ **Search Functionality**: Most list pages have search fields  
✓ **Pagination**: Tables show 20 items per page  
✓ **Role-Based Access**: Features appear based on your role  
✓ **Auto-Login**: Check "Remember me" to stay logged in  
✓ **Mobile Friendly**: Responsive design works on mobile devices  

---

## Troubleshooting

### Can't login
- Check username and password (case-sensitive)
- Default is `admin` / `admin`
- Ensure user account is active (Director can disable accounts)

### Template not found error
- Make sure you're in the project root directory
- Check virtual environment is activated
- Restart the application

### Database locked
- Close other connections to the database
- Delete `.db-journal` file if it exists
- Restart the application

### Port 5000 already in use
- Change FLASK_PORT in .env file
- Or kill the process using port 5000

---

## Next Steps

1. **Change Admin Password**: Go to Users → Edit User (for admin)
2. **Register Staff**: Create H2, Warden, Office, Director accounts
3. **Register Students**: Register student accounts
4. **Setup Initial Data**: Add medicines, assets, etc.
5. **Customize Settings**: Edit config.py as needed

---

## Support

For issues or questions:
1. Check the README.md for detailed documentation
2. Review the project structure in [app/](app/)
3. Check database models in [app/models.py](app/models.py)
4. Review routes for specific blueprint modules

---

**Happy Managing!** 🏥🏠
