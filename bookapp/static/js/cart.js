document.addEventListener('DOMContentLoaded', function() {
    // Elements
    const modal = document.getElementById('deliveryMethodModal');
    const deliveryOptions = document.querySelectorAll('.delivery-option');
    const homeForm = document.getElementById('homeDeliveryForm');
    const storeForm = document.getElementById('storePickupForm');
    const confirmBtn = document.getElementById('confirmDelivery');
    const closeBtn = document.querySelector('.close');

    // Initialize all functionalities
    initializeCartButtons();
    initializeModal();
    initializeSelectionFeatures();

    // Initialize cart buttons for add, update, delete actions
    function initializeCartButtons() {
        // Add to cart
        const addToCartButtons = document.querySelectorAll('.add-to-cart');
        addToCartButtons.forEach(button => {
            button.addEventListener('click', function(e) {
                e.preventDefault();
                addToCart(this.dataset.id, this.dataset.name, this.dataset.price);
            });
        });

        // Decrease quantity
        const minusButtons = document.querySelectorAll('.btn-minus');
        minusButtons.forEach(button => {
            button.addEventListener('click', function() {
                const row = this.closest('tr');
                const productId = row.querySelector('td a').innerText;
                updateQuantity(productId, -1);
            });
        });

        // Increase quantity
        const plusButtons = document.querySelectorAll('.btn-plus');
        plusButtons.forEach(button => {
            button.addEventListener('click', function() {
                const row = this.closest('tr');
                const productId = row.querySelector('td a').innerText;
                updateQuantity(productId, 1);
            });
        });

        // Delete product
        const deleteButtons = document.querySelectorAll('.fa-trash');
        deleteButtons.forEach(button => {
            button.closest('button').addEventListener('click', function() {
                const row = this.closest('tr');
                const productId = row.querySelector('td a').innerText;
                deleteFromCart(productId);
            });
        });

        // Initialize payment button
        document.querySelector('.cart-btn button:nth-child(2)').addEventListener('click', function() {
            processPayment();
        });
    }

    // Initialize selection features
    function initializeSelectionFeatures() {
        const selectAllCheckbox = document.getElementById('selectAll');
        const productCheckboxes = document.querySelectorAll('.product-select');

        if (selectAllCheckbox) {
            selectAllCheckbox.addEventListener('change', toggleAllProducts);
        }

        productCheckboxes.forEach(checkbox => {
            checkbox.addEventListener('change', updateSelectedTotal);
        });

        // Reset selected products when loading page
        sessionStorage.removeItem('selectedProducts');
    }

    // Initialize modal functionality
    function initializeModal() {
        // Show modal when clicking delivery method button
        document.querySelector('.cart-btn button:first-child').addEventListener('click', function() {
            modal.style.display = 'block';
        });

        // Close modal functionality
        closeBtn.addEventListener('click', closeModal);
        window.addEventListener('click', function(event) {
            if (event.target === modal) {
                closeModal();
            }
        });

        // Handle delivery method selection
        deliveryOptions.forEach(option => {
            option.addEventListener('click', function() {
                deliveryOptions.forEach(opt => {
                    opt.classList.remove('active', 'btn-secondary');
                    opt.classList.add('btn-primary');
                });

                this.classList.add('active', 'btn-secondary');
                this.classList.remove('btn-primary');

                const method = this.dataset.method;
                homeForm.style.display = method === 'home' ? 'block' : 'none';
                storeForm.style.display = method === 'store' ? 'block' : 'none';
            });
        });

        // Handle delivery information confirmation
        confirmBtn.addEventListener('click', saveDeliveryInfo);
    }
});

// Selection functions
function toggleAllProducts() {
    const selectAllCheckbox = document.getElementById('selectAll');
    const productCheckboxes = document.querySelectorAll('.product-select');

    productCheckboxes.forEach(checkbox => {
        checkbox.checked = selectAllCheckbox.checked;
    });

    updateSelectedTotal();
}

function updateSelectedTotal() {
    let totalQuantity = 0;
    let totalAmount = 0;

    // Get all selected checkboxes
    const selectedProducts = document.querySelectorAll('.product-select:checked');

    selectedProducts.forEach(checkbox => {
        const quantity = parseInt(checkbox.dataset.quantity);
        const price = parseFloat(checkbox.dataset.price);

        totalQuantity += quantity;
        totalAmount += quantity * price;
    });

    // Update display
    const totalProductsElement = document.querySelector('.cart-content p:first-child span');
    const totalPriceElement = document.querySelector('.cart-content h4 span');

    if (totalProductsElement && totalPriceElement) {
        totalProductsElement.innerText = totalQuantity;
        totalPriceElement.innerText = new Intl.NumberFormat('vi-VN').format(totalAmount) + ' VND';
    }

    // Save selected products to sessionStorage
    const selectedProductIds = Array.from(selectedProducts).map(checkbox => checkbox.dataset.id);
    sessionStorage.setItem('selectedProducts', JSON.stringify(selectedProductIds));
}

// Cart API functions
function addToCart(id, name, price) {
    fetch('/api/add-cart', {
        method: 'POST',
        body: JSON.stringify({
            'id': id,
            'name': name,
            'price': price
        }),
        headers: {
            'Content-Type': 'application/json'
        }
    }).then(res => res.json()).then(data => {
        if (data.code === 200) {
            let cartCounter = document.getElementById('cart-counter');
            document.getElementById('cartCounter').innerText = data.data.total_quantity;
            if (cartCounter)
                cartCounter.innerText = data.data.total_quantity;
            alert('Thêm sản phẩm vào giỏ hàng thành công!');
        } else {
            alert(data.message);
        }
    }).catch(err => console.error(err));
}

function updateQuantity(productId, change) {
    fetch('/api/update-cart', {
        method: 'POST',
        body: JSON.stringify({
            'id': productId,
            'change': change
        }),
        headers: {
            'Content-Type': 'application/json'
        }
    }).then(res => res.json())
    .then(data => {
        if (data.code === 200) {
            // Update product quantity and total
            const quantityInput = document.querySelector(`#quantity-${productId}`);
            const totalElement = document.querySelector(`#total-${productId}`);
            const checkbox = document.querySelector(`.product-select[data-id="${productId}"]`);

            quantityInput.value = data.updated_quantity;
            totalElement.innerText = new Intl.NumberFormat('vi-VN').format(data.updated_total) + ' VND';

            // Update checkbox data attributes
            if (checkbox) {
                checkbox.dataset.quantity = data.updated_quantity;
                checkbox.dataset.price = data.updated_total / data.updated_quantity;
                if (checkbox.checked) {
                    updateSelectedTotal();
                }
            }

            // Update cart counter
            const cartCounter = document.getElementById('cartCounter');
            if (cartCounter) {
                cartCounter.innerText = data.cart_total_quantity;
            }
        } else if (data.code === 400) {
            Swal.fire({
                icon: 'error',
                title: 'Không thể thêm sản phẩm',
                text: 'Số lượng sản phẩm trong kho không đủ',
                confirmButtonText: 'Đóng'
            });

            const quantityInput = document.querySelector(`#quantity-${productId}`);
            quantityInput.value = data.current_quantity;
        }
    })
    .catch(err => {
        console.error('Error:', err);
        Swal.fire({
            icon: 'error',
            title: 'Lỗi',
            text: 'Đã có lỗi xảy ra khi cập nhật giỏ hàng',
            confirmButtonText: 'Đóng'
        });
    });
}

function deleteFromCart(productId) {
    fetch('/api/delete-cart', {
        method: 'POST',
        body: JSON.stringify({
            'id': productId
        }),
        headers: {
            'Content-Type': 'application/json'
        }
    }).then(res => res.json())
    .then(data => {
        document.getElementById(`product-${productId}`).remove();
        updateCartSummary(data.cart_total_quantity, data.cart_total_price);

        if (data.cart_total_quantity === 0) {
            location.reload();
        }
    });
}

// Modal functions
function saveDeliveryInfo() {
    const selectedOption = document.querySelector('.delivery-option.active');
    if (!selectedOption) {
        alert('Vui lòng chọn phương thức nhận hàng!');
        return;
    }

    const deliveryMethod = selectedOption.dataset.method;
    const form = deliveryMethod === 'home' ?
                 document.getElementById('homeDeliveryForm') :
                 document.getElementById('storePickupForm');

    // Validate required fields
    const requiredInputs = form.querySelectorAll('[required]');
    for (let input of requiredInputs) {
        if (!input.value) {
            alert('Vui lòng điền đầy đủ thông tin bắt buộc!');
            return;
        }
    }

    // Validate payment method
    const paymentMethod = form.querySelector(`input[name="${deliveryMethod}Payment"]:checked`);
    if (!paymentMethod) {
        alert('Vui lòng chọn phương thức thanh toán!');
        return;
    }

    // Collect form data
    let deliveryInfo = {
        delivery_method: deliveryMethod,
        payment_method: paymentMethod.value,
        phone: form.querySelector('input[type="tel"]').value,
        email: form.querySelector('input[type="email"]').value
    };

    if (deliveryMethod === 'home') {
        deliveryInfo.delivery_address = [
            form.querySelector('input[placeholder="Địa chỉ cụ thể"]').value,
            form.querySelector('input[placeholder="Xã/phường"]').value,
            form.querySelector('input[placeholder="Quận/huyện"]').value,
            form.querySelector('input[placeholder="Tỉnh/thành phố"]').value
        ].join(', ');
    }

    sessionStorage.setItem('deliveryInfo', JSON.stringify(deliveryInfo));
    alert('Thêm thông tin thành công!');
    closeModal();
}

function processPayment() {
    const selectedProducts = JSON.parse(sessionStorage.getItem('selectedProducts') || '[]');

    if (selectedProducts.length === 0) {
        Swal.fire({
            icon: 'warning',
            title: 'Chưa chọn sản phẩm',
            text: 'Vui lòng chọn ít nhất một sản phẩm để thanh toán!',
            confirmButtonText: 'Đóng'
        });
        return;
    }

    const deliveryInfo = JSON.parse(sessionStorage.getItem('deliveryInfo'));
    if (!deliveryInfo) {
        alert('Vui lòng chọn phương thức nhận hàng trước khi thanh toán!');
        return;
    }

    fetch('/api/pay', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            ...deliveryInfo,
            selectedProducts: selectedProducts
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.code === 200) {
            sessionStorage.removeItem('deliveryInfo');
            sessionStorage.removeItem('selectedProducts');
            alert('Đặt hàng thành công!');
            window.location.href = '/';
        } else {
            alert('Có lỗi xảy ra khi đặt hàng!');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Có lỗi xảy ra khi đặt hàng!');
    });
}

function closeModal() {
    const modal = document.getElementById('deliveryMethodModal');
    const homeForm = document.getElementById('homeDeliveryForm');
    const storeForm = document.getElementById('storePickupForm');

    modal.style.display = 'none';
    homeForm.style.display = 'none';
    storeForm.style.display = 'none';
    homeForm.reset();
    storeForm.reset();
}

// Utility functions
function formatPrice(price) {
    return new Intl.NumberFormat('vi-VN').format(price) + ' VND';
}

function updateCartSummary(quantity, price) {
    const cartCounter = document.getElementById('cartCounter');
    const totalProductsElement = document.querySelector('.cart-content p:first-child span');
    const totalPriceElement = document.querySelector('.cart-content h4 span');

    if (cartCounter) cartCounter.innerText = quantity;
    if (totalProductsElement) totalProductsElement.innerText = quantity;
    if (totalPriceElement) totalPriceElement.innerText = formatPrice(price);
}