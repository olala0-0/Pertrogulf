# 💾 Web Save Discard Button

| | |
|---|---|
| **Author** | ERP Addons |
| **Website** | https://www.erp-addons.com |
| **Version** | 19.0.1.0.0 |
| **License** | OPL-1 |
| **Odoo** | 19.0 |

---

# 📖 Overview

**Web Save Discard Button** improves the Odoo form editing experience by providing clearly labeled **Save** and **Discard** buttons.

The module makes record editing easier by presenting direct actions for confirming or cancelling changes. Users can quickly save valid modifications or discard unwanted edits without changing the standard Odoo record workflow.

---

# 🚀 Key Features

## 💾 Clear Save Button

The module provides a clearly labeled **Save** button for confirming changes made while editing a record.

**Save Action**

`Save`

The Save button allows users to confirm and apply their current changes.

---

## 🗑️ Clear Discard Button

The module provides a clearly labeled **Discard** button for cancelling unwanted changes.

**Discard Action**

`Discard`

The Discard button allows users to cancel their current edits and return the record to its previous state.

---

## 🖥️ Improved Form Editing

The module improves the usability of Odoo form views by making the primary editing actions easier to identify.

Users can clearly distinguish between:

- Save changes
- Discard changes

This provides a more intuitive record editing workflow.

---

## 🔄 Simple Editing Workflow

The module provides a straightforward workflow for managing record changes.

### Save

Confirm the changes made to the record and apply them.

### Discard

Cancel the current changes and restore the previous record state.

---

# ⚙️ Installation

1. Copy the **web_save_discard_button** module into your Odoo addons directory.
2. Restart the Odoo server.
3. Update the Apps List.

**📍 Menu Navigation**

`Apps → Update Apps List`

4. Search for **Web Save Discard Button**.
5. Click **Install**.

The module integrates with the standard Odoo web interface.

---

# 📖 Usage

## 📝 Edit a Record

Open any supported Odoo form and start editing the record.

The available editing actions can be used to manage the current changes.

---

## 💾 Save Changes

Click:

`Save`

The current changes are confirmed and applied to the record.

---

## 🗑️ Discard Changes

Click:

`Discard`

The current edits are cancelled and the previous record values are restored.

---

## 🔄 Manage Record Changes

Use the Save and Discard actions according to the required workflow:

- **Save** to keep and apply changes.
- **Discard** to cancel unwanted changes.

This makes the form editing process clearer and easier to use.

---

# 🏗️ Architecture

```
web_save_discard_button
│
├── Form Editing Interface
│   ├── Save Button
│   └── Discard Button
│
└── Web Form Workflow
    ├── Confirm Changes
    └── Cancel Changes

```

---

# 🔧 Technical Details

The module extends the Odoo web form editing interface to provide clear Save and Discard actions.

The module is designed to work with the standard Odoo form editing workflow without changing the underlying business logic of records.

The main functionality includes:

```
Save
Discard
```

The module focuses on improving the visibility and usability of record editing actions.

---

# 📌 Changelog

## 19.0.1.0.0 — Initial Release

- Added clearly labeled Save button.
- Added clearly labeled Discard button.
- Improved the Odoo form editing workflow.
- Simplified confirmation and cancellation of record changes.
- Integrated Save and Discard actions into the web form interface.

---

# 💬 Support

For questions, feature requests, or technical support, please visit:

🌐 **https://www.erp-addons.com**