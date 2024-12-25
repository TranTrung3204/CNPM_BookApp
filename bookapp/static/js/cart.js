document.addEventListener('DOMContentLoaded', function() {
    // Elements
    const modal = document.getElementById('deliveryMethodModal');
    const deliveryOptions = document.querySelectorAll('.delivery-option');
    const homeForm = document.getElementById('homeDeliveryForm');
    const storeForm = document.getElementById('storePickupForm');
    const confirmBtn = document.getElementById('confirmDelivery');
    const closeBtn = document.querySelector('.close');

    // Cart functionality
    initializeCartButtons();

    // Modal functionality
    initializeModal();

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
                updateQuantity(productId, -1, row);
            });
        });

        // Increase quantity
        const plusButtons = document.querySelectorAll('.btn-plus');
        plusButtons.forEach(button => {
            button.addEventListener('click', function() {
                const row = this.closest('tr');
                const productId = row.querySelector('td a').innerText;
                updateQuantity(productId, 1, row);
            });
        });

        // Delete product
        const deleteButtons = document.querySelectorAll('.fa-trash');
        deleteButtons.forEach(button => {
            button.closest('button').addEventListener('click', function() {
                const row = this.closest('tr');
                const productId = row.querySelector('td a').innerText;
                deleteProduct(productId, row);
            });
        });

        // Initialize payment button
        document.querySelector('.cart-btn button:nth-child(2)').addEventListener('click', function() {
            if (!sessionStorage.getItem('deliveryInfo')) {
                alert('Vui lòng chọn phương thức nhận hàng trước khi thanh toán!');
                return;
            }
            processPayment();
        });
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

    // Save delivery information to session storage
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

        // Add delivery address for home delivery
        if (deliveryMethod === 'home') {
            deliveryInfo.delivery_address = [
                form.querySelector('input[placeholder="Địa chỉ cụ thể"]').value,
                form.querySelector('input[placeholder="Xã/phường"]').value,
                form.querySelector('input[placeholder="Quận/huyện"]').value,
                form.querySelector('input[placeholder="Tỉnh/thành phố"]').value
            ].join(', ');
        }

        // Save delivery info to session storage
        sessionStorage.setItem('deliveryInfo', JSON.stringify(deliveryInfo));

        // Show success message and close modal
        alert('Thêm thông tin thành công!');
        closeModal();
    }

    // Process payment
    function processPayment() {
        const deliveryInfo = JSON.parse(sessionStorage.getItem('deliveryInfo'));
        if (!deliveryInfo) {
            alert('Vui lòng chọn phương thức nhận hàng trước khi thanh toán!');
            return;
        }

        // Send payment request
        fetch('/api/pay', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(deliveryInfo)
        })
        .then(response => response.json())
        .then(data => {
            if (data.code === 200) {
                // Clear delivery info from session storage
                sessionStorage.removeItem('deliveryInfo');
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

    // Close modal
    function closeModal() {
        modal.style.display = 'none';
        homeForm.style.display = 'none';
        storeForm.style.display = 'none';
        homeForm.reset();
        storeForm.reset();
    }
});

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
            // Cập nhật số lượng giỏ hàng
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

            quantityInput.value = data.updated_quantity;
            totalElement.innerText = new Intl.NumberFormat('vi-VN').format(data.updated_total) + ' VND';

            // Update cart counter
            const cartCounter = document.getElementById('cartCounter');
            if (cartCounter) {
                cartCounter.innerText = data.cart_total_quantity;
            }

            // Update cart summary
            updateCartSummary(data.cart_total_quantity, data.cart_total_price);
        } else if (data.code === 400) {
            // Handle insufficient stock
            Swal.fire({
                icon: 'error',
                title: 'Không thể thêm sản phẩm',
                text: 'Số lượng sản phẩm trong kho không đủ',
                confirmButtonText: 'Đóng'
            });

            // Revert quantity input to previous value
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

function updateCartSummary(quantity, price) {
    // Update total products
    const totalProductsElement = document.querySelector('.cart-content p:first-child span');
    if (totalProductsElement) {
        totalProductsElement.innerText = quantity;
    }

    // Update total price
    const totalPriceElement = document.querySelector('.cart-content h4 span');
    if (totalPriceElement) {
        totalPriceElement.innerText = new Intl.NumberFormat('vi-VN').format(price) + ' VND';
    }

    // Update cart counter if exists
    const cartCounter = document.getElementById('cartCounter');
    if (cartCounter) {
        cartCounter.innerText = quantity;
    }
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
        // Xóa dòng sản phẩm
        document.getElementById(`product-${productId}`).remove();

        // Cập nhật tổng số lượng và tổng tiền
        document.getElementById('cartCounter').innerText = data.cart_total_quantity;
        document.querySelector('.cart-content p:first-child span').innerText =
            data.cart_total_quantity;
        document.querySelector('.cart-content h4 span').innerText =
            new Intl.NumberFormat('vi-VN').format(data.cart_total_price) + ' VND';

        // Kiểm tra nếu giỏ hàng trống
        if (data.cart_total_quantity === 0) {
            location.reload(); // Tải lại trang để hiện thông báo giỏ hàng trống
        }
    });
}

function formatPrice(price) {
    return price.toLocaleString('en-US', {
        minimumFractionDigits: 1,
        maximumFractionDigits: 1
    }) + ' VND';
}

function updateCartSummary(quantity, price) {
    document.getElementById('cartCounter').innerText = quantity;
    document.querySelector('.cart-summary h4 span').innerText = formatPrice(price);
}
