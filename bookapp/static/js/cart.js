document.addEventListener('DOMContentLoaded', function() {
    // Lắng nghe sự kiện click trên nút "Thêm vào giỏ"
    const addToCartButtons = document.querySelectorAll('.add-to-cart');
    addToCartButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const bookId = this.dataset.id;
            const bookName = this.dataset.name;
            const bookPrice = this.dataset.price;

            // Gửi yêu cầu thêm sản phẩm vào giỏ hàng
            addToCart(bookId, bookName, bookPrice);
        });
    });

    // Lắng nghe sự kiện click trên nút giảm số lượng
    const minusButtons = document.querySelectorAll('.btn-minus');
    minusButtons.forEach(function(button) {
        button.addEventListener('click', function(event) {
            const row = this.closest('tr');
            const productId = row.querySelector('td a').innerText;
            updateQuantity(productId, -1, row);  // Gọi hàm giảm số lượng
        });
    });

    // Lắng nghe sự kiện click trên nút tăng số lượng
    const plusButtons = document.querySelectorAll('.btn-plus');
    plusButtons.forEach(function(button) {
        button.addEventListener('click', function(event) {
            const row = this.closest('tr');
            const productId = row.querySelector('td a').innerText;
            updateQuantity(productId, 1, row);  // Gọi hàm tăng số lượng
        });
    });

    // Lắng nghe sự kiện click trên nút xóa sản phẩm
    const deleteButtons = document.querySelectorAll('.fa-trash');
    deleteButtons.forEach(function(button) {
        button.closest('button').addEventListener('click', function() {
            const row = this.closest('tr');
            const productId = row.querySelector('td a').innerText;
            deleteProduct(productId, row);  // Gọi hàm xóa sản phẩm
        });
    });
});

// Hàm thêm sản phẩm vào giỏ hàng
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
    })
    .then(response => response.json())
    .then(data => {
        // Kiểm tra nếu mã trạng thái là 401 (chưa đăng nhập)
        if (data.code === 401) {
            // Hiển thị thông báo
            alert(data.message);
            // Chuyển hướng đến trang đăng nhập
            window.location.href = '/user-login';
        } else {
            // Cập nhật số lượng giỏ hàng trên header
            document.getElementById('cartCounter').innerText = data.total_quantity;

            // Thêm hiệu ứng thông báo thêm sản phẩm thành công
            alert('Đã thêm sản phẩm vào giỏ hàng');
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
}

// Hàm cập nhật số lượng sản phẩm trong giỏ hàng
function updateQuantity(productId, change, row) {
    fetch('/api/update-cart', {
        method: 'POST',
        body: JSON.stringify({
            id: productId,
            change: change
        }),
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(function(response) {
        return response.json();
    })
    .then(function(data) {
        row.querySelector('.qty input').value = data.updated_quantity;

        const totalCell = row.querySelector('td:nth-child(4)');
        totalCell.innerText = formatPrice(data.updated_total);

        document.querySelector('#cartCounter').innerText = data.cart_total_quantity;
        document.querySelector('.cart-summary h4 span').innerText = formatPrice(data.cart_total_price);
    })
    .catch(function(err) {
        console.error('Error:', err);
    });
}

// Hàm xóa sản phẩm khỏi giỏ
function deleteProduct(productId, row) {
    fetch('/api/delete-cart', {
        method: 'POST',
        body: JSON.stringify({ id: productId }),
        headers: { 'Content-Type': 'application/json' }
    })
    .then(response => response.json())
    .then(data => {
        row.remove();  // Xóa dòng sản phẩm khỏi bảng

        // Kiểm tra nếu giỏ hàng rỗng
        if (data.cart_total_quantity === 0) {
            const table = document.querySelector('.table-responsive');
            table.innerHTML = '<h4>Không có sản phẩm nào trong giỏ!</h4>';
        }

        document.querySelector('#cartCounter').innerText = data.cart_total_quantity;
        document.querySelector('.cart-summary h4 span').innerText = formatPrice(data.cart_total_price);
    })
    .catch(function(err) {
        console.error('Error:', err);
    });
}

// Hàm định dạng giá tiền
function formatPrice(price) {
    return price.toLocaleString('en-US', {
        minimumFractionDigits: 1,
        maximumFractionDigits: 1
    }) + ' VND';
}

// Hàm thanh toán
function pay() {
    if (confirm('Do you want to pay?') == true) {
        fetch('/api/pay', { method: 'POST' })
            .then(function(res) {
                return res.json();
            })
            .then(function(data) {
                if (data.code == 200) {
                    location.reload();
                }
            })
            .catch(function(err) {
                console.error(err);
            });
    }
}
