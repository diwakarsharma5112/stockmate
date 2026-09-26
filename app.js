function updateRow(select) {
    const row = select.closest('.bill-row');
    const option = select.options[select.selectedIndex];
    const qty = row.querySelector('input[name="quantity"]');
    const gst = row.querySelector('input[name="item_gst"]');
    if (option.dataset.stock) qty.max = option.dataset.stock;
    if (option.dataset.gst !== undefined) gst.value = option.dataset.gst;
    const image = row.querySelector('.bill-product-image');
    if (image) { image.src = option.dataset.image || image.src; image.alt = option.textContent.trim(); }
    calculateTotal();
}

function calculateTotal() {
    let subtotal = 0;
    const rows = document.querySelectorAll('.bill-row');
    rows.forEach(row => {
        const select = row.querySelector('select[name="product_id"]');
        const qtyInput = row.querySelector('input[name="quantity"]');
        const gstInput = row.querySelector('input[name="item_gst"]');
        const lineTotal = row.querySelector('.line-total');
        const option = select.options[select.selectedIndex];
        const price = parseFloat(option?.dataset.price || 0);
        const qty = parseInt(qtyInput.value || 0);
        const line = price * qty;
        lineTotal.value = '₹' + line.toFixed(2);
        subtotal += line;
    });
    const discountPercent = parseFloat(document.getElementById('discountPercent')?.value || 0);
    const discount = subtotal * discountPercent / 100;
    const discountFactor = subtotal ? (subtotal - discount) / subtotal : 0;
    let gst = 0;
    rows.forEach(row => {
        const select = row.querySelector('select[name="product_id"]');
        const qtyInput = row.querySelector('input[name="quantity"]');
        const gstInput = row.querySelector('input[name="item_gst"]');
        const option = select.options[select.selectedIndex];
        const price = parseFloat(option?.dataset.price || 0);
        const qty = parseInt(qtyInput.value || 0);
        const rate = parseFloat(gstInput.value || option?.dataset.gst || 0);
        gst += price * qty * discountFactor * rate / 100;
    });
    const total = subtotal - discount + gst;
    document.getElementById('subtotal').textContent = '₹' + subtotal.toFixed(2);
    document.getElementById('discountAmount').textContent = '- ₹' + discount.toFixed(2);
    document.getElementById('gstAmount').textContent = '₹' + gst.toFixed(2);
    document.getElementById('grandTotal').textContent = '₹' + total.toFixed(2);
}

function removeRow(button) {
    const rows = document.querySelectorAll('.bill-row');
    if (rows.length > 1) {
        button.closest('.bill-row').remove();
        calculateTotal();
    }
}

function addRow() {
    const container = document.getElementById('billRows');
    const first = container.querySelector('.bill-row');
    const clone = first.cloneNode(true);
    clone.querySelector('select').selectedIndex = 0;
    const image = clone.querySelector('.bill-product-image');
    if (image) { image.src = image.dataset.default || image.src; image.alt = 'Product'; }
    clone.querySelector('input[name="quantity"]').value = 1;
    clone.querySelector('input[name="item_gst"]').value = 18;
    clone.querySelector('.line-total').value = '₹0.00';
    container.appendChild(clone);
    calculateTotal();
}

document.addEventListener('DOMContentLoaded', calculateTotal);
