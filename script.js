// Global variables
const API_BASE_URL = 'http://127.0.0.1:8000/api';
let currentUser = null;
let authToken = null;

// DOM elements
const hamburger = document.querySelector('.hamburger');
const navMenu = document.querySelector('.nav-menu');
const loginBtn = document.getElementById('login-btn');
const registerBtn = document.getElementById('register-btn');
const profileLink = document.getElementById('profile-link');
const loginModal = document.getElementById('login-modal');
const registerModal = document.getElementById('register-modal');
const bookingModal = document.getElementById('booking-modal');
const loading = document.getElementById('loading');
const notification = document.getElementById('notification');

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
    setupEventListeners();
    loadAirports();
    checkAuthStatus();
});

// Initialize application
function initializeApp() {
    // Set minimum date to today
    const today = new Date().toISOString().split('T')[0];
    document.getElementById('departure-date').min = today;
    document.getElementById('return-date').min = today;
    
    // Set return date minimum to departure date
    document.getElementById('departure-date').addEventListener('change', function() {
        document.getElementById('return-date').min = this.value;
    });
}

// Setup event listeners
function setupEventListeners() {
    // Mobile menu toggle
    hamburger.addEventListener('click', toggleMobileMenu);
    
    // Navigation links
    document.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('click', handleNavClick);
    });
    
    // Modal buttons
    loginBtn.addEventListener('click', () => openModal('login-modal'));
    registerBtn.addEventListener('click', () => openModal('register-modal'));
    
    // Modal close buttons
    document.querySelectorAll('.close').forEach(closeBtn => {
        closeBtn.addEventListener('click', closeModal);
    });
    
    // Modal switch links
    document.getElementById('switch-to-register').addEventListener('click', (e) => {
        e.preventDefault();
        closeModal();
        openModal('register-modal');
    });
    
    document.getElementById('switch-to-login').addEventListener('click', (e) => {
        e.preventDefault();
        closeModal();
        openModal('login-modal');
    });
    
    // Forms
    document.getElementById('login-form').addEventListener('submit', handleLogin);
    document.getElementById('register-form').addEventListener('submit', handleRegister);
    document.getElementById('flight-search-form').addEventListener('submit', handleFlightSearch);
    document.getElementById('booking-form').addEventListener('submit', handleBooking);
    document.getElementById('profile-form').addEventListener('submit', handleProfileUpdate);
    document.getElementById('contact-form').addEventListener('submit', handleContactForm);
    
    // Tab functionality
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', handleTabClick);
    });
    
    // Search tabs
    document.querySelectorAll('[data-tab]').forEach(btn => {
        btn.addEventListener('click', handleSearchTabClick);
    });
    
    // Click outside modal to close
    window.addEventListener('click', (e) => {
        if (e.target.classList.contains('modal')) {
            closeModal();
        }
    });
}

// Mobile menu toggle
function toggleMobileMenu() {
    hamburger.classList.toggle('active');
    navMenu.classList.toggle('active');
}

// Navigation click handler
function handleNavClick(e) {
    e.preventDefault();
    const targetId = e.target.getAttribute('href').substring(1);
    
    // Close mobile menu
    hamburger.classList.remove('active');
    navMenu.classList.remove('active');
    
    // Update active nav link
    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.remove('active');
    });
    e.target.classList.add('active');
    
    // Show/hide sections
    if (targetId === 'profile') {
        if (!currentUser) {
            showNotification('Please login to view your profile', 'error');
            openModal('login-modal');
            return;
        }
        showProfileSection();
    } else {
        hideAllSections();
        if (targetId === 'home') {
            document.getElementById('home').style.display = 'block';
        } else if (targetId === 'flights') {
            document.getElementById('flights').style.display = 'block';
            loadFlights();
        } else if (targetId === 'about') {
            document.getElementById('about').style.display = 'block';
        } else if (targetId === 'contact') {
            document.getElementById('contact').style.display = 'block';
        }
    }
}

// Show profile section
function showProfileSection() {
    hideAllSections();
    document.getElementById('profile').style.display = 'block';
    loadUserProfile();
    loadUserBookings();
}

// Hide all sections
function hideAllSections() {
    document.querySelectorAll('section').forEach(section => {
        section.style.display = 'none';
    });
}

// Modal functions
function openModal(modalId) {
    document.getElementById(modalId).style.display = 'block';
}

function closeModal() {
    document.querySelectorAll('.modal').forEach(modal => {
        modal.style.display = 'none';
    });
}

// Tab functionality
function handleTabClick(e) {
    const tabId = e.target.getAttribute('data-tab');
    
    // Update tab buttons
    e.target.parentElement.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    e.target.classList.add('active');
    
    // Update tab content
    e.target.parentElement.parentElement.querySelectorAll('.tab-pane').forEach(pane => {
        pane.classList.remove('active');
    });
    document.getElementById(tabId).classList.add('active');
}

// Search tab functionality
function handleSearchTabClick(e) {
    const tabType = e.target.getAttribute('data-tab');
    
    // Update tab buttons
    document.querySelectorAll('.search-tabs .tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    e.target.classList.add('active');
    
    // Show/hide return date
    const returnDateGroup = document.getElementById('return-date-group');
    if (tabType === 'one-way') {
        returnDateGroup.style.display = 'none';
        document.getElementById('return-date').required = false;
    } else {
        returnDateGroup.style.display = 'block';
        document.getElementById('return-date').required = true;
    }
}

// Authentication functions
async function checkAuthStatus() {
    const token = localStorage.getItem('authToken');
    if (token) {
        authToken = token;
        try {
            const response = await fetch(`${API_BASE_URL}/accounts/me/`, {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
            
            if (response.ok) {
                currentUser = await response.json();
                updateAuthUI();
            } else {
                localStorage.removeItem('authToken');
                authToken = null;
            }
        } catch (error) {
            console.error('Auth check failed:', error);
            localStorage.removeItem('authToken');
            authToken = null;
        }
    }
}

function updateAuthUI() {
    if (currentUser) {
        loginBtn.style.display = 'none';
        registerBtn.style.display = 'none';
        profileLink.style.display = 'block';
        profileLink.innerHTML = `<i class="fas fa-user"></i> ${currentUser.first_name}`;
    } else {
        loginBtn.style.display = 'block';
        registerBtn.style.display = 'block';
        profileLink.style.display = 'none';
    }
}

// Login handler
async function handleLogin(e) {
    e.preventDefault();
    showLoading(true);
    
    const formData = new FormData(e.target);
    const loginData = {
        email: formData.get('email'),
        password: formData.get('password')
    };
    
    try {
        const response = await fetch(`${API_BASE_URL}/accounts/login/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(loginData)
        });
        
        const data = await response.json();
        
        if (response.ok) {
            authToken = data.access;
            localStorage.setItem('authToken', authToken);
            currentUser = data.user;
            updateAuthUI();
            closeModal();
            showNotification('Login successful!', 'success');
        } else {
            showNotification(data.detail || 'Login failed', 'error');
        }
    } catch (error) {
        showNotification('Network error. Please try again.', 'error');
    } finally {
        showLoading(false);
    }
}

// Register handler
async function handleRegister(e) {
    e.preventDefault();
    showLoading(true);
    
    const formData = new FormData(e.target);
    const registerData = {
        first_name: formData.get('first_name'),
        last_name: formData.get('last_name'),
        username: formData.get('username'),
        email: formData.get('email'),
        date_of_birth: formData.get('date_of_birth'),
        password: formData.get('password'),
        password2: formData.get('password2')
    };
    
    if (registerData.password !== registerData.password2) {
        showNotification('Passwords do not match', 'error');
        showLoading(false);
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/accounts/register/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(registerData)
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showNotification('Registration successful! Please login.', 'success');
            closeModal();
            openModal('login-modal');
        } else {
            const errorMessage = data.detail || Object.values(data).flat().join(', ');
            showNotification(errorMessage, 'error');
        }
    } catch (error) {
        showNotification('Network error. Please try again.', 'error');
    } finally {
        showLoading(false);
    }
}

// Load airports
async function loadAirports() {
    try {
        const response = await fetch(`${API_BASE_URL}/flight/airports/`);
        const data = await response.json();
        
        const departureSelect = document.getElementById('departure-airport');
        const arrivalSelect = document.getElementById('arrival-airport');
        
        // Clear existing options
        departureSelect.innerHTML = '<option value="">Select departure airport</option>';
        arrivalSelect.innerHTML = '<option value="">Select arrival airport</option>';
        
        // Add airport options
        data.results.forEach(airport => {
            const option1 = new Option(`${airport.name} (${airport.city})`, airport.id);
            const option2 = new Option(`${airport.name} (${airport.city})`, airport.id);
            departureSelect.add(option1);
            arrivalSelect.add(option2);
        });
    } catch (error) {
        console.error('Failed to load airports:', error);
    }
}

// Flight search handler
async function handleFlightSearch(e) {
    e.preventDefault();
    showLoading(true);
    
    const formData = new FormData(e.target);
    const searchParams = {
        departure_airport: formData.get('departure_airport'),
        arrival_airport: formData.get('arrival_airport'),
        departure_time: formData.get('departure_date'),
        passengers: formData.get('passengers')
    };
    
    // Add return date if round trip
    const isRoundTrip = document.querySelector('[data-tab="round-trip"]').classList.contains('active');
    if (isRoundTrip && formData.get('return_date')) {
        searchParams.return_time = formData.get('return_date');
    }
    
    try {
        const queryString = new URLSearchParams(searchParams).toString();
        const response = await fetch(`${API_BASE_URL}/flight/flights/?${queryString}`);
        const data = await response.json();
        
        displayFlights(data.results);
        showNotification(`Found ${data.results.length} flights`, 'info');
    } catch (error) {
        showNotification('Failed to search flights', 'error');
    } finally {
        showLoading(false);
    }
}

// Display flights
function displayFlights(flights) {
    const container = document.getElementById('flights-container');
    
    if (flights.length === 0) {
        container.innerHTML = '<p class="text-center">No flights found for your search criteria.</p>';
        return;
    }
    
    container.innerHTML = flights.map(flight => `
        <div class="flight-card" data-flight-id="${flight.id}">
            <div class="flight-header">
                <span class="flight-number">${flight.flight_number}</span>
                <span class="flight-status status-${flight.status}">${flight.status}</span>
            </div>
            <div class="flight-route">
                <div class="route-info">
                    <div class="airport-code">${flight.departure_airport.city}</div>
                    <div class="airport-name">${flight.departure_airport.name}</div>
                </div>
                <div class="flight-duration">
                    <i class="fas fa-plane"></i>
                    <div>${formatDuration(flight.departure_time, flight.arrival_time)}</div>
                </div>
                <div class="route-info">
                    <div class="airport-code">${flight.arrival_airport.city}</div>
                    <div class="airport-name">${flight.arrival_airport.name}</div>
                </div>
            </div>
            <div class="flight-time">
                <div>${formatTime(flight.departure_time)}</div>
                <div>${formatTime(flight.arrival_time)}</div>
            </div>
            <div class="flight-footer">
                <div class="airline-info">
                    <div class="airline-logo">${flight.airplane.airline.name.charAt(0)}</div>
                    <div class="airline-name">${flight.airplane.airline.name}</div>
                </div>
                <div class="flight-price">$${Math.floor(Math.random() * 500) + 200}</div>
                <button class="book-btn" onclick="openBookingModal(${flight.id})">Book Now</button>
            </div>
        </div>
    `).join('');
}

// Load all flights
async function loadFlights() {
    showLoading(true);
    try {
        const response = await fetch(`${API_BASE_URL}/flight/flights/`);
        const data = await response.json();
        displayFlights(data.results);
    } catch (error) {
        showNotification('Failed to load flights', 'error');
    } finally {
        showLoading(false);
    }
}

// Open booking modal
function openBookingModal(flightId) {
    if (!currentUser) {
        showNotification('Please login to book a flight', 'error');
        openModal('login-modal');
        return;
    }
    
    // Find flight data
    const flightCard = document.querySelector(`[data-flight-id="${flightId}"]`);
    if (!flightCard) return;
    
    const flightNumber = flightCard.querySelector('.flight-number').textContent;
    const departure = flightCard.querySelector('.airport-code').textContent;
    const arrival = flightCard.querySelectorAll('.airport-code')[1].textContent;
    const price = flightCard.querySelector('.flight-price').textContent;
    
    document.getElementById('booking-details').innerHTML = `
        <div class="booking-details">
            <h3>Flight ${flightNumber}</h3>
            <p>${departure} → ${arrival}</p>
            <p>Price: ${price}</p>
        </div>
    `;
    
    document.getElementById('booking-form').setAttribute('data-flight-id', flightId);
    document.querySelector('input[name="price"]').value = price.replace('$', '');
    
    openModal('booking-modal');
}

// Booking handler
async function handleBooking(e) {
    e.preventDefault();
    showLoading(true);
    
    const formData = new FormData(e.target);
    const flightId = e.target.getAttribute('data-flight-id');
    
    const bookingData = {
        flight: flightId,
        seat_number: formData.get('seat_number'),
        price: formData.get('price')
    };
    
    try {
        const response = await fetch(`${API_BASE_URL}/flight/tickets/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify(bookingData)
        });
        
        if (response.ok) {
            showNotification('Booking successful!', 'success');
            closeModal();
            loadUserBookings();
        } else {
            const data = await response.json();
            showNotification(data.detail || 'Booking failed', 'error');
        }
    } catch (error) {
        showNotification('Network error. Please try again.', 'error');
    } finally {
        showLoading(false);
    }
}

// Load user profile
async function loadUserProfile() {
    if (!currentUser) return;
    
    document.getElementById('profile-name').textContent = currentUser.get_full_name || `${currentUser.first_name} ${currentUser.last_name}`;
    document.getElementById('profile-email').textContent = currentUser.email;
    
    // Populate edit form
    document.getElementById('edit-first-name').value = currentUser.first_name;
    document.getElementById('edit-last-name').value = currentUser.last_name;
    document.getElementById('edit-email').value = currentUser.email;
    document.getElementById('edit-dob').value = currentUser.date_of_birth || '';
}

// Load user bookings
async function loadUserBookings() {
    if (!currentUser) return;
    
    try {
        const response = await fetch(`${API_BASE_URL}/flight/tickets/`, {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });
        
        const data = await response.json();
        displayBookings(data.results);
    } catch (error) {
        console.error('Failed to load bookings:', error);
    }
}

// Display bookings
function displayBookings(bookings) {
    const container = document.getElementById('bookings-list');
    
    if (bookings.length === 0) {
        container.innerHTML = '<p>No bookings found.</p>';
        return;
    }
    
    container.innerHTML = bookings.map(booking => `
        <div class="booking-item">
            <div class="booking-info">
                <h4>Flight ${booking.flight.flight_number}</h4>
                <p>${booking.flight.departure_airport.city} → ${booking.flight.arrival_airport.city}</p>
                <p>Seat: ${booking.seat_number} | Price: $${booking.price}</p>
                <p>Date: ${formatDate(booking.flight.departure_time)}</p>
            </div>
            <div class="booking-status status-${booking.status}">${booking.status}</div>
        </div>
    `).join('');
}

// Profile update handler
async function handleProfileUpdate(e) {
    e.preventDefault();
    showLoading(true);
    
    const formData = new FormData(e.target);
    const updateData = {
        first_name: formData.get('first_name'),
        last_name: formData.get('last_name'),
        email: formData.get('email'),
        date_of_birth: formData.get('date_of_birth')
    };
    
    try {
        const response = await fetch(`${API_BASE_URL}/accounts/profile/update/`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify(updateData)
        });
        
        if (response.ok) {
            const updatedUser = await response.json();
            currentUser = updatedUser;
            loadUserProfile();
            showNotification('Profile updated successfully!', 'success');
        } else {
            const data = await response.json();
            showNotification(data.detail || 'Update failed', 'error');
        }
    } catch (error) {
        showNotification('Network error. Please try again.', 'error');
    } finally {
        showLoading(false);
    }
}

// Contact form handler
function handleContactForm(e) {
    e.preventDefault();
    showNotification('Thank you for your message! We will get back to you soon.', 'success');
    e.target.reset();
}

// Utility functions
function showLoading(show) {
    loading.style.display = show ? 'block' : 'none';
}

function showNotification(message, type = 'info') {
    notification.textContent = message;
    notification.className = `notification ${type}`;
    notification.classList.add('show');
    
    setTimeout(() => {
        notification.classList.remove('show');
    }, 5000);
}

function formatTime(dateString) {
    return new Date(dateString).toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit'
    });
}

function formatDate(dateString) {
    return new Date(dateString).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    });
}

function formatDuration(departure, arrival) {
    const dep = new Date(departure);
    const arr = new Date(arrival);
    const diff = arr - dep;
    const hours = Math.floor(diff / (1000 * 60 * 60));
    const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
    return `${hours}h ${minutes}m`;
}

// Smooth scrolling for anchor links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
});

// Add scroll effect to navbar
window.addEventListener('scroll', function() {
    const navbar = document.querySelector('.navbar');
    if (window.scrollY > 100) {
        navbar.style.background = 'rgba(255, 255, 255, 0.98)';
        navbar.style.boxShadow = '0 2px 20px rgba(0, 0, 0, 0.15)';
    } else {
        navbar.style.background = 'rgba(255, 255, 255, 0.95)';
        navbar.style.boxShadow = '0 2px 20px rgba(0, 0, 0, 0.1)';
    }
});

// Initialize animations on scroll
const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -50px 0px'
};

const observer = new IntersectionObserver(function(entries) {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.style.opacity = '1';
            entry.target.style.transform = 'translateY(0)';
        }
    });
}, observerOptions);

// Observe elements for animation
document.querySelectorAll('.feature-card, .flight-card, .contact-item').forEach(el => {
    el.style.opacity = '0';
    el.style.transform = 'translateY(30px)';
    el.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
    observer.observe(el);
});
