# Credit Limit Module for Odoo

This module adds credit limit functionality to the Odoo customer management system. It allows administrators to set an authorized credit limit for customers and automatically calculates the available credit based on outstanding invoices.

## Features

- **Credito Autorizado**: A field to set the authorized credit limit for each customer.
- **Credito Disponible**: A computed field that calculates the available credit as the difference between the authorized credit limit and the total amount pending payment on invoices.
- **Sale Order Validation**: Before confirming a sale order, the system checks if the available credit is sufficient. If not, a warning message is displayed, preventing the confirmation.

## Installation

1. Place the `credit_limit` directory in your Odoo addons path.
2. Update the app list in Odoo.
3. Install the `credit_limit` module from the Apps menu.

## Usage

- Navigate to the customer form view to set or modify the `Credito Autorizado` field.
- When creating a sale order, the system will automatically check the `Credito Disponible` before allowing confirmation.

## Dependencies

- Odoo version 14.0 or higher.
- The `sale` module must be installed.

## Author

Your Name

## License

This module is licensed under the MIT License.