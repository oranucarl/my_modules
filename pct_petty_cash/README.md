# Petty Cash Management (pct_petty_cash)

**Version:** 18.0.1.0.1
**Category:** Accounting/Accounting
**License:** LGPL-3
**Website:** https://www.packetclouds.com

## Overview

This Odoo 18 module provides a comprehensive petty cash management system where users can manage petty cash operations as custodians.

## Features

### Document States
- **Draft** - Initial setup phase, configuration fields can be modified
- **Running** - Active operations, allocations and expenses can be recorded
- **Closed** - Year-end closed, no modifications allowed

### Main Form
The petty cash form contains the following fields:

1. **Petty Cash Name** - Custodian project name
2. **Petty Cash Journal** - Cash journal for custodian transactions
3. **Custodian Account** - Readonly, automatically set from journal's default account
4. **Amount Allocated (Current Year)** - Computed sum of posted allocations in current year
5. **Amount Expensed (Current Year)** - Computed sum of posted expenses in current year
6. **Amount Left** - Computed balance (Brought Forward + Allocated - Expensed)
7. **Amount Brought Forward** - **Computed** balance from previous years (all posted allocations - all posted expenses before current year)

### Tab 1: Allocations
Rows of all amounts issued to custodians:
- **Payment Date** - Date of allocation
- **Amount Allocated** - Amount being allocated
- **Source Journal** - Company bank/cash journal where payment is made from
- **Source Account** - Readonly, from source journal
- **Analytic Distribution** - For cost tracking
- **Journal Entry** - Generated journal entry
- **Status** - Draft/Posted
- **Post Button** - Posts the journal entry (creates if not exists)

**Journal Entry Lines:**
- Debit: Custodian Account (Cash GL)
- Credit: Source Account (Bank/Cash GL)

### Tab 2: Expenses
Rows of all expenses made by custodian:
- **Expense Category** - Product/service for categorization
- **Description** - Expense description
- **Amount Spent** - Amount expensed
- **Expense Account** - From product category
- **Expense Date** - Date of expense
- **Analytic Distribution** - For cost tracking
- **Journal Entry** - Generated journal entry
- **Status** - Draft/Posted
- **Post Button** - Posts the journal entry (creates if not exists)

**Journal Entry Lines:**
- Debit: Expense Account (from product)
- Credit: Custodian Account (Cash GL)

### Sorting
Both tabs display newer records at the top (descending date order).

## Security

### User Groups

1. **Petty Cash Users (PCU)**
   - Can view only their own petty cash records
   - Cannot edit form fields or lines directly
   - Can use wizards to create allocation requests and expense lines
   - Cannot see Post buttons

2. **Petty Cash Accountants (PCA)**
   - Can view all custodian records
   - Can modify all lines
   - Can post journal entries
   - Post buttons are visible

3. **Petty Cash Managers (PCM)**
   - Full access to all features
   - Can create/delete petty cash records
   - Can modify configuration
   - Includes all PCA permissions

### Record Rules
- Users see only records where they are the custodian
- Accountants and Managers see all records
- Multi-company support with company-based filtering

## Wizards

### Allocation Request Wizard
Available to all users to request allocations:
- Payment Date
- Amount Requested
- Source Journal (where payment will come from)
- Analytic Distribution

### Expense Wizard
Available to all users to record expenses:
- Expense Date
- Expense Category (Product)
- Description
- Amount Spent
- Analytic Distribution

## Dependencies

- `account` - Accounting base module
- `analytic` - Analytic accounting

## Installation

1. Copy the module to your Odoo addons directory
2. Update the apps list
3. Install "Petty Cash Management" from the Apps menu

## Usage

1. **Setup:**
   - Create a cash journal for each custodian
   - Assign users to appropriate security groups

2. **Create Petty Cash Record:**
   - Go to Petty Cash > All Petty Cash (as Accountant/Manager)
   - Create new record with custodian user and journal
   - Set "Amount Brought Forward" if applicable

3. **For Custodians (Users):**
   - Go to Petty Cash > My Petty Cash
   - Click "Request Allocation" to create allocation requests
   - Click "Record Expense" to record expenses

4. **For Accountants:**
   - Review allocation and expense lines
   - Click "Post" to create and post journal entries
   - View journal entries via "View Entry" button

## Technical Details

### Models
- `pct.petty.cash` - Main petty cash record
- `pct.petty.cash.allocation` - Allocation lines
- `pct.petty.cash.expense` - Expense lines
- `pct.petty.cash.allocation.wizard` - Allocation request wizard
- `pct.petty.cash.expense.wizard` - Expense recording wizard

### Inheritance
- `mail.thread` - For activity tracking
- `mail.activity.mixin` - For scheduled activities
- `analytic.mixin` - For analytic distribution support

## Changelog

### 18.0.1.0.0
- Initial release for Odoo 18
- Petty cash custodian management
- Allocation and expense tracking
- Automatic journal entry creation
- Three-level security model
- Wizard-based data entry for users
