# PCT Expatriate Management Module

Complete Odoo 18 module for comprehensive expatriate employee management.

## Features

### Core Functionality
- **Expatriate Employee Tracking** via employee tags
- **Two-way sync** between expatriate tag and non-resident status
- **Monthly Allowance Tracking** with Year/Month grouping
- **Housing Management** with lease renewal alerts
- **Document Tracking** (Residence Permits, CERPEC, Work Permits, Visas) with expiry alerts
- **Sponsor Company** master data management
- **Replica Payroll Menus** (contracts, payslips, batches) filtered to expatriate data only
- **Daily Cron Job** for automatic expiry date recalculation

### Security
- Restricted to **Expatriate Payroll Manager** access group only
- All models have record rules limiting access to the expatriate group
- Reuses security group from `pct_payroll_expatriate` module

## Module Structure

```
pct_expatriate_management/
├── __manifest__.py
├── __init__.py
├── models/
│   ├── __init__.py
│   ├── hr_employee_category.py       # Adds is_expatriate field to tags
│   ├── hr_employee.py                # Two-way sync logic
│   ├── expatriate_sponsor_company.py # Sponsor companies master data
│   ├── expatriate_allowance.py       # Monthly allowances with workflow
│   ├── expatriate_housing.py         # Housing with renewal alerts
│   └── expatriate_document.py        # Documents with expiry tracking
├── security/
│   ├── security.xml                  # Record rules
│   └── ir.model.access.csv           # Access rights
├── data/
│   ├── default_data.xml              # Default tag, sponsors, sequence
│   └── cron.xml                      # Daily expiry recalculation job
├── views/
│   ├── hr_employee_category_views.xml
│   ├── expatriate_sponsor_company_views.xml
│   ├── expatriate_allowance_views.xml
│   ├── expatriate_housing_views.xml
│   ├── expatriate_document_views.xml
│   └── menu.xml                      # Complete menu structure
└── static/
    └── description/
        └── icon.png                  # Module icon (PENDING - see below)
```

## Installation

### Prerequisites
- Odoo 18 Community Edition or Enterprise
- `pct_payroll_expatriate` module installed

### Steps
1. Place this module in your Odoo addons directory
2. **IMPORTANT**: Save the provided icon image to `static/description/icon.png`
3. Update the apps list: Settings → Apps → Update Apps List
4. Search for "PCT Expatriate Management"
5. Click Install

## Menu Structure

The module creates a top-level "Expatriate Management" application with:

```
Expatriate Management
├── Employees (filtered to expatriate tags)
├── Payroll
│   ├── Contracts (expatriate only)
│   ├── Payslip Batches (expatriate only)
│   └── All Payslips (expatriate only)
├── Allowances (grouped by Year > Month)
├── Housing (with renewal alerts)
├── Documents (all types with filtering)
└── Configuration
    ├── Employee Tags (expatriate tags only)
    └── Sponsor Companies
```

## Key Models

### expatriate.allowance
- Sequential numbering (EXP-ALW/YYYY/0001)
- Three-state workflow: Draft → Confirmed → Paid
- Domain-filtered to expatriate employees only
- Default grouped by Year > Month

### expatriate.housing
- Auto-computed name from employee + location
- Alert status: Expired, Urgent (<30 days), Due Soon (30-60 days), Safe (>60 days)
- Total cost calculation from rent + maintenance + electricity
- Daily cron recomputes days_to_expire

### expatriate.document
- Support for: Residence Permit, CERPEC, Work Permit, Visa, Other
- Tracks both passport expiry and document expiry
- Alert status with same thresholds as housing
- Daily cron recomputes days_left

### expatriate.sponsor.company
- Simple master data: Name, Code, Notes
- Pre-loaded with: ALM CD, ALM SS, AMEC, SCHNEIDER, Shahin Construction

## Two-Way Sync Logic

### Employee Tag ↔ Non-Resident Status
- **Tag added** → `is_non_resident` = True
- **Tag removed** → `is_non_resident` = False
- **is_non_resident checked** → Expatriate tag added
- **is_non_resident unchecked** → Expatriate tag removed
- Uses `skip_expat_sync` context to prevent infinite loops
- Works in UI (onchange) and backend (write override)

## Alert Status Badge Colors

### In List Views
- **Expired**: Red (danger)
- **Urgent** (<30 days): Red (danger)
- **Due Soon** (30-60 days): Yellow (warning)
- **Safe** (>60 days): Green (success)

## Default Data

### Employee Tag
- Name: "Expatriate"
- Color: 4 (blue)
- is_expatriate: True

### Sponsor Companies
1. ALM CD
2. ALM SS
3. AMEC
4. SCHNEIDER
5. Shahin Construction

## Cron Jobs

### Expatriate: Recompute Expiry Dates
- **Frequency**: Daily
- **Models**: expatriate.housing, expatriate.document
- **Action**: Recomputes days_to_expire and days_left for all active records
- **Purpose**: Keeps alert statuses current without manual intervention

## Technical Notes

- **Odoo 18 Compatibility**: Uses `@api.model_create_multi`, `fields.Date.today()`, proper depends
- **Stored Computed Fields**: days_to_expire, days_left, alert_status are stored for filtering/sorting
- **Mail Integration**: Allowance, Housing, Document models inherit mail.thread and mail.activity.mixin
- **Employee Domain**: All employee_id fields use `domain="[('category_ids.is_expatriate', '=', True)]"`
- **Badge Widget**: Alert status fields use `widget="badge"` with color decorations
- **Application Flag**: `application: True` creates top-level app menu

## TODO

1. **Save Icon**: Place the provided "Expatriate odoo" icon image at:
   ```
   static/description/icon.png
   ```
   The module expects this file to exist for the app icon to display properly.

2. **Test Installation**: Install on a fresh database with `pct_payroll_expatriate` already installed

3. **Verify Security**: Confirm only users with "Expatriate Payroll Manager" can access the app

4. **Test Two-Way Sync**: Add/remove expatriate tag and verify is_non_resident syncs correctly

## License
LGPL-3

## Author
PCT

## Version
18.0.1.0.0
