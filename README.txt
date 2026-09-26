STOCKMATE - UPDATED FLASK INVENTORY & BILLING SYSTEM

Features:
- Home dashboard
- Inventory management
- Add, edit and remove products
- Low-stock alerts
- Product search bar
- Billing and printable invoices
- Discount and 18% GST calculation
- Cash, UPI, Card and Other payment methods
- Sales history
- Sales reports/dashboard
- Top products and payment summary
- Support, About and Contact pages

RUN THE PROJECT
1. Open this folder in VS Code.
2. Open Terminal -> New Terminal.
3. If the terminal is already inside this folder, do not use cd.
4. Install Flask:
   python -m pip install -r requirements.txt
5. Start the application:
   python app.py
6. Open in your browser:
   http://127.0.0.1:5000

IMPORTANT
- Use `python -m pip`, not just `pip`, if Windows says pip is not recognized.
- The database file inventory.db is created automatically when the app starts.
- Existing databases are automatically updated with the new billing fields.
- GST is currently set to 18% in app.py.
- Low-stock warning is currently 5 or fewer units.
