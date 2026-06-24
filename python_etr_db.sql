-- Clean Unified E-Commerce Database Schema
-- Consolidates location hierarchy, user management, cart/checkout, and order tracking

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
SET FOREIGN_KEY_CHECKS = 0;
SET AUTOCOMMIT = 0;
START TRANSACTION;
SET time_zone = "+00:00";

-- Increase timeout and packet size to prevent disconnection
SET SESSION wait_timeout = 28800;
SET SESSION interactive_timeout = 28800;
SET SESSION max_allowed_packet = 67108864;

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

-- ========================================
-- DROP EXISTING TABLES (if any)
-- ========================================
DROP TABLE IF EXISTS `contact_messages`;
DROP TABLE IF EXISTS `payments`;
DROP TABLE IF EXISTS `order_status_history`;
DROP TABLE IF EXISTS `orderitems`;
DROP TABLE IF EXISTS `orders`;
DROP TABLE IF EXISTS `inventories`;
DROP TABLE IF EXISTS `cartitems`;
DROP TABLE IF EXISTS `cart`;
DROP TABLE IF EXISTS `guestcart`;
DROP TABLE IF EXISTS `products`;
DROP TABLE IF EXISTS `categories`;
DROP TABLE IF EXISTS `users`;
DROP TABLE IF EXISTS `barangays`;
DROP TABLE IF EXISTS `municipalities`;
DROP TABLE IF EXISTS `provinces`;

-- ========================================
-- LOCATION HIERARCHY TABLES
-- ========================================

CREATE TABLE `provinces` (
  `province_id` int(11) NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `province_name` varchar(100) NOT NULL,
  UNIQUE KEY `province_name` (`province_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

INSERT INTO `provinces` (`province_id`, `province_name`) VALUES
(1, 'Ilocos Norte'),
(2, 'Ilocos Sur'),
(3, 'La Union'),
(4, 'Pangasinan');

CREATE TABLE `municipalities` (
  `municipality_id` int(11) NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `municipality_name` varchar(100) NOT NULL,
  `province_id` int(11) NOT NULL,
  KEY `province_id` (`province_id`),
  CONSTRAINT `municipalities_ibfk_1` FOREIGN KEY (`province_id`) REFERENCES `provinces` (`province_id`) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

INSERT INTO `municipalities` (`municipality_id`, `municipality_name`, `province_id`) VALUES
(1, 'Agno', 4),
(2, 'Aguilar', 4),
(3, 'Alaminos City', 4),
(4, 'Alcala', 4),
(12, 'Binalonan', 4),
(18, 'Dagupan City', 4),
(46, 'Urdaneta City', 4),
(58, 'Bacarra', 1),
(61, 'Batac City', 1),
(63, 'Laoag City', 1);

CREATE TABLE `barangays` (
  `barangay_id` int(11) NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `barangay_name` varchar(150) NOT NULL,
  `municipality_id` int(11) NOT NULL,
  KEY `municipality_id` (`municipality_id`),
  CONSTRAINT `barangays_ibfk_1` FOREIGN KEY (`municipality_id`) REFERENCES `municipalities` (`municipality_id`) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

INSERT INTO `barangays` (`barangay_id`, `barangay_name`, `municipality_id`) VALUES
(116, 'Mangcasuy', 12),
(455, 'Nancayasan', 46),
(460, 'Sta. Lucia', 46);

-- ========================================
-- USERS TABLE
-- ========================================

CREATE TABLE `users` (
  `user_id` int(11) NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `firstname` varchar(255) NOT NULL,
  `middlename` varchar(255),
  `lastname` varchar(255) NOT NULL,
  `email` varchar(255) NOT NULL,
  `phone` varchar(11) NOT NULL,
  `province` int(11) NOT NULL,
  `municipality` int(11) NOT NULL,
  `barangay` int(11) NOT NULL,
  `password` varchar(255) NOT NULL,
  `role` enum('Admin','Customer','Guest') DEFAULT 'Customer',
  `status` tinyint(4) DEFAULT 1,
  `created_at` datetime DEFAULT current_timestamp(),
  UNIQUE KEY `email` (`email`),
  KEY `idx_role` (`role`),
  CONSTRAINT `users_province_fk` FOREIGN KEY (`province`) REFERENCES `provinces` (`province_id`) ON DELETE RESTRICT,
  CONSTRAINT `users_municipality_fk` FOREIGN KEY (`municipality`) REFERENCES `municipalities` (`municipality_id`) ON DELETE RESTRICT,
  CONSTRAINT `users_barangay_fk` FOREIGN KEY (`barangay`) REFERENCES `barangays` (`barangay_id`) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

INSERT INTO `users` (`user_id`, `firstname`, `middlename`, `lastname`, `email`, `phone`, `province`, `municipality`, `barangay`, `password`, `role`, `status`) VALUES
(14, 'Juan', 'Dina', 'Tamad', 'juan@gmail.com', '09987654321', 4, 12, 116, 'scrypt:32768:8:1$51MkVgqQkpzq9Q1t$314aaba8c9227cce639b66aaf2d418d97d2c482e7ce4ab601d4828c9623a63b3fc8fcc465c2375c1149763e1ad4c78f0e7c565f6ef80ce600202c43a444531aa', 'Customer', 0),
(15, 'Peter', 'Pick', 'Parker', 'peter@gmail.com', '09121043332', 4, 46, 455, 'scrypt:32768:8:1$k9Yj16JEyy34DLpK$e4f1e89e81662032bbf7ba43762844e65868f8d0c3b79dca87224bdaf3c1ce6bb039835060f719535c0a3660cd7780ac7ea7edf9a8990becc09dc4addc8fc49c', 'Customer', 1),
(16, 'Carlo', 'Sira', 'Yulo', 'carlo@gmail.com', '09121043332', 4, 46, 460, 'scrypt:32768:8:1$QZTvySWyP8pA1nWz$648a61078b3ea8fabd81d394d13a95c9c58836b319a1f03b170a34f630052e4e8bf45a861b3a267958acbe58278b5d68d2b77bf240f2d47429e9509ff066e4b2', 'Customer', 1);

-- ========================================
-- CATEGORIES TABLE
-- ========================================

CREATE TABLE `categories` (
  `category_id` int(11) NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `name` varchar(250) NOT NULL,
  `description` text
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

INSERT INTO `categories` (`category_id`, `name`, `description`) VALUES
(1, 'Dog Food', 'Nutritious wet and dry food options specifically formulated for puppies and adult dogs.'),
(2, 'Milk & Milk Replacers', 'Lactose-free milk and nutrient-rich milk replacers for puppies, kittens, and other small mammals.'),
(3, 'Dry Cat Food', 'Premium kibble formulated for indoor cats, kittens, and specific health needs like urinary and skin care.'),
(4, 'Wet Cat Food', 'Gourmet flakes, chunks in gravy, and jelly-based wet food for felines of all life stages.'),
(5, 'Dog Treats', 'Dental chews and flavored biscuits designed to reward your dog and promote oral hygiene.'),
(6, 'Cat Treats', 'Crunchy bites, lickable purees, and savory snacks that cats crave.');

-- ========================================
-- PRODUCTS TABLE (Single source of truth for stock)
-- ========================================

CREATE TABLE `products` (
  `product_id` int(11) NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `name` varchar(250) NOT NULL,
  `description` text NOT NULL,
  `price` decimal(10,2) NOT NULL DEFAULT 0,
  `category` int(11) NOT NULL,
  `img_path` varchar(250) NOT NULL,
  `stock` int(11) NOT NULL DEFAULT 0,
  `visible` tinyint(4) DEFAULT 1,
  `created_at` datetime DEFAULT current_timestamp(),
  KEY `category_fk` (`category`),
  CONSTRAINT `products_category_fk` FOREIGN KEY (`category`) REFERENCES `categories` (`category_id`) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

INSERT INTO `products` (`product_id`, `name`, `description`, `price`, `category`, `img_path`, `stock`) VALUES
(1, 'Special Delight Adult Smoked Chicken with Mixed Veggies Wet Dog Food 130g (10 pouches)', 'Formulated with high quality ingredients to meet nutritional needs of adult dogs. Offers essential vitamins, minerals and high-quality protein.', 350.00, 1, '/uploads/products/Special Delight Adult Smoked Chicken with Mixed Veggies Wet Dog Food 130g (10 pouches).png', 42),
(2, 'Special Delight Adult Salmon Flavor Chunk in Gravy Wet Dog Food 130g (10 pouches)', 'Rich in omega-3 fatty acids, Packed with Vitamin D and B vitamins to promote strong bones and healthy immune system.', 350.00, 1, '/uploads/products/Special Delight Adult Salmon Flavor Chunk in Gravy Wet Dog Food 130g (10 pouches).png', 15),
(3, 'Special Delight Puppy Roast Beef Chunk in Gravy Wet Dog Food 130g (10 pouches)', 'Made with premium ingredients to meet the nutritional needs of growing puppies. Ultimate choice for nourishing during crucial early years.', 350.00, 1, '/uploads/products/Special Delight Puppy Roast Beef Chunk in Gravy Wet Dog Food 130g (10 pouches).png', 28),
(4, 'Special Delight Adult Roast Beef Chunk in Gravy Wet Dog Food 130g (10 pouches)', 'Formulated with essential vitamins and minerals to support immune function and healthy skin for overall vitality.', 350.00, 1, '/uploads/products/Special Delight Adult Roast Beef Chunk in Gravy Wet Dog Food 130g (10 pouches).png', 11),
(5, 'Special Delight Adult Chicken Chunk in Gravy Wet Dog Food 130g (10 pouches)', 'Good source of high-quality protein for muscle maintenance. Savory gravy makes the food highly appealing to pets.', 350.00, 1, '/uploads/products/Special Delight Adult Chicken Chunk in Gravy Wet Dog Food 130g (10 pouches).png', 34),
(6, 'Pedigree Adult Beef Chunks in Gravy Wet Dog Food 130g (12 pouches)', 'Complete and Balanced Nutrition with Omega 6 and Zinc for healthy skin and shiny coat.', 492.00, 1, '/uploads/products/Pedigree Adult Beef Chunks in Gravy Wet Dog Food 130g (12 pouches).png', 29),
(7, 'Pedigree Adult Beef Wet Dog Food 400g (3 cans)', 'Meaty chunks produced from quality meat and selected vegetables. Enriched with Vitamin E and Omega 6.', 375.00, 1, '/uploads/products/Pedigree Adult Beef Wet Dog Food 400g (3 cans).png', 17),
(8, 'Pedigree Adult Chicken and Liver with Gravy Wet Dog Food 130g (12 pouches)', 'Chicken and Liver Chunks Flavor in Gravy. Contains Calcium and Phosphorus for strong bones and teeth.', 492.00, 1, '/uploads/products/Pedigree Adult Chicken and Liver with Gravy Wet Dog Food 130g (12 pouches).png', 38),
(9, 'Pedigree Puppy Chicken Chunks in Gravy Wet Dog Food 130g (12 pouches)', 'Meaty chunks for enjoyment. Provides complete nutrition for the body system to work effectively.', 540.00, 1, '/uploads/products/Pedigree Puppy Chicken Chunks in Gravy Wet Dog Food 130g (12 pouches).png', 45),
(10, 'Pedigree Puppy Wet Dog Food 400g (3 cans)', 'Home Style for Puppy. Carefully cooked to preserve the essential nutritions needed for growth.', 390.00, 1, '/uploads/products/Pedigree Puppy Wet Dog Food 400g (3 cans).png', 22),
(11, 'Pedigree Adult Chicken and Liver Wet Dog Food 400g (3 cans)', 'Enriched with Vitamin E and Omega 6 for healthy skin and a beautiful coat. Superb taste from real meat.', 375.00, 1, '/uploads/products/Pedigree Adult Chicken and Liver Wet Dog Food 400g (3 cans).png', 13),
(12, 'Cosi Pet\'s Milk 1L (2 cartons)', 'Lactose Free milk from Australia cow\'s milk. For cats and dogs of all breeds and life stages.', 400.00, 2, '/uploads/products/Cosi Pet\'s Milk 1L (2 cartons).png', 50),
(13, 'Puppy Sure Goat\'s Milk Replacer 250g', 'Highly Digestible & Palatable with Low Lactose Content. Rich in Vitamins, Minerals, Enzymes, and Protein.', 719.00, 2, '/uploads/products/Puppy Sure Goat\'s Milk Replacer 250g.png', 10),
(14, 'Royal Canin Feline Care Nutrition Adult Urinary Care Dry Cat Food 2kg', 'Precisely balanced nutritional formula which helps maintain urinary tract health in 10 days.', 1550.00, 3, '/uploads/products/Royal Canin Feline Care Nutrition Adult Urinary Care Dry Cat Food 2kg.png', 19),
(15, 'SmartHeart Adult Chicken and Tuna Dry Cat Food 1.2kg', 'Promote Brain Function with DHA and Choline. Taurine supplement for healthy eyesight.', 310.00, 3, '/uploads/products/SmartHeart Adult Chicken and Tuna Dry Cat Food 1.2kg.png', 25),
(16, 'Royal Canin Feline Care Nutrition Adult Hair and Skin Dry Cat Food 2kg', 'Exclusive complex of nutrients which helps support the skin barrier role and coat shine.', 1550.00, 3, '/uploads/products/Royal Canin Feline Care Nutrition Adult Hair and Skin Dry Cat Food 2kg.png', 12),
(17, 'Royal Canin Feline Health Nutrition Adult Indoor 27 Dry Cat Food 2kg', 'Stool Odour Reduction and Hairball Reduction for indoor cats with lower activity levels.', 1360.00, 3, '/uploads/products/Royal Canin Feline Health Nutrition Adult Indoor 27 Dry Cat Food 2kg.png', 31),
(18, 'SmartHeart Kitten Chicken Fresh Egg and Milk Dry Cat Food 1.1kg', 'Protein from eggs and milk for development of muscle and proper body structure in kittens.', 320.00, 3, '/uploads/products/SmartHeart Kitten Chicken Fresh Egg and Milk Dry Cat Food 1.1kg.png', 44),
(19, 'Royal Canin Feline Health Nutrition Kitten Dry Cat Food 2kg', 'Immune System Support with a patented complex of antioxidants. High energy content for growth.', 1550.00, 3, '/uploads/products/Royal Canin Feline Health Nutrition Kitten Dry Cat Food 2kg.png', 18),
(20, 'Sheba Succulent Chicken Breast Wet Cat Food 85g (6 cans)', 'Delicate fine flakes carefully coated in a delicious gravy. No artificial colors or flavors.', 420.00, 4, '/uploads/products/Sheba Succulent Chicken Breast Wet Cat Food 85g (6 cans).png', 26),
(21, 'SmartHeart Refine Adult Tuna with Crab Stick in Jelly Wet Cat Food 70g (12 pouches)', 'Selected premium white meat tuna prepared in delicate gourmet recipes. Absolute Fine Dining.', 504.00, 4, '/uploads/products/SmartHeart Refine Adult Tuna with Crab Stick in Jelly Wet Cat Food 70g (12 pouches).png', 37),
(22, 'SmartHeart Refine Adult Tuna with Bonito in Jelly Wet Cat Food 70g (12 pouches)', 'Exquisite menu of gourmet cat food manufactured to exceptional quality and safety standards.', 504.00, 4, '/uploads/products/SmartHeart Refine Adult Tuna with Bonito in Jelly Wet Cat Food 70g (12 pouches).png', 41),
(23, 'Sheba Adult Tuna and Salmon Wet Cat Food 70g (12 pouches)', 'Complete and balanced food. Delicate fine flakes carefully coated in a delicious gravy.', 540.00, 4, '/uploads/products/Sheba Adult Tuna and Salmon Wet Cat Food 70g (12 pouches).png', 22),
(24, 'Kit Cat Grain-Free Tuna and Mackerel Wet Cat Food 400g (2 cans)', 'Rich In Omega 3 and Omega 6. Reduces risk of kidney stones and urinary tract infection.', 190.00, 4, '/uploads/products/Kit Cat Grain-Free Tuna and Mackerel Wet Cat Food 400g (2 cans).png', 20),
(25, 'Kit Cat Deboned Chicken and Beef Wet Cat Food 80g (6 cans)', '100% grain free diet. Supports a healthy lifestyle and pH level balance.', 354.00, 4, '/uploads/products/Kit Cat Deboned Chicken and Beef Wet Cat Food 80g (6 cans).png', 14),
(26, 'Kit Cat Grain-Free Tuna and Katsoubushi Wet Cat Food 400g (2 cans)', 'Human Grade Quality. Essential vitamins help keep feline eyesight healthy.', 190.00, 4, '/uploads/products/Kit Cat Grain-Free Tuna and Katsoubushi Wet Cat Food 400g (2 cans).png', 21),
(27, 'Pedigree Dentastix Puppy 4-12 Months Dog Treats 7s 56g (2 packs)', 'With Anti-tartar ingredient. High Calcium, Low Fat and No Sugar Added for puppies.', 158.00, 5, '/uploads/products/Pedigree Dentastix Puppy 4-12 Months Dog Treats 7s 56g (2 packs).png', 49),
(28, 'SmartHeart Fruit and Vegetable Dog Treats 100g', 'Natural nutrition and vitamins from Banana, Carrot, Blueberry and Cranberry.', 85.00, 5, '/uploads/products/SmartHeart Fruit and Vegetable Dog Treats 100g.png', 32),
(29, 'Absolute Holistic Dental Chew Peanut Butter Dog Treats 25g', 'Uniquely shaped to act like a toothbrush to effectively scrape plaque and tartar.', 49.00, 5, '/uploads/products/Absolute Holistic Dental Chew Peanut Butter Dog Treats 25g.png', 39),
(30, 'SmartHeart Grilled Beef Dog Treats 100g', 'Omega 6 promotes healthy skin and coat. Special designed shape reduces plaque.', 85.00, 5, '/uploads/products/SmartHeart Grilled Beef Dog Treats 100g.png', 23),
(31, 'Absolute Holistic Dental Chew Milk Dog Treats 25g', 'Addition of milk aids in strengthening teeth and bones with the presence of calcium.', 49.00, 5, '/uploads/products/Absolute Holistic Dental Chew Milk Dog Treats 25g.png', 18),
(32, 'SmartHeart Grilled Chicken Dog Treats 100g', 'Natural Cellulose helps to support digestive system working properly.', 85.00, 5, '/uploads/products/SmartHeart Grilled Chicken Dog Treats 100g.png', 27),
(33, 'Pedigree Dentastix Toy 2-5kg Dog Treats 7s 60g (2 packs)', 'Unique X-Shape. Helps reduce plaque and tartar build up to keep teeth and gums healthy.', 178.00, 5, '/uploads/products/Pedigree Dentastix Toy 2-5kg Dog Treats 7s 60g (2 packs).png', 16),
(34, 'Temptations Salmon Cat Treats 75g', 'Scrumptious, crunchy outer shell with an irresistibly soft, tasty center.', 115.00, 6, '/uploads/products/Temptations Salmon Cat Treats 75g.png', 30),
(35, 'Temptations Chicken Cat Treats 75g', '100% nutritionally complete. No artificial flavours; real flavors they crave.', 115.00, 6, '/uploads/products/Temptations Chicken Cat Treats 75g.png', 35),
(36, 'Ciao Churu Grilled Tuna Scallop Cat Treats 12gx4 (4R-105) (2 packs)', 'Contains Vitamin E and Green Tea extract to help reduce cholesterol and blood sugar.', 220.00, 6, '/uploads/products/Ciao Churu Grilled Tuna Scallop Cat Treats 12gx4 (4R-105) (2 packs).png', 48),
(37, 'Ciao Churu Tuna Maguro Cat Treats 14gx4 (SC-71) (2 packs)', 'Lickable treat for all Life Stages. Provides oral support for healthier teeth and gums.', 220.00, 6, '/uploads/products/Ciao Churu Tuna Maguro Cat Treats 14gx4 (SC-71) (2 packs).png', 39),
(38, 'Ciao Churu Chicken Fillet Cat Treats 14gx4 (SC-73) (2 packs)', 'Refrigerate after opening. High quality treat to supplement cat\'s nutritional needs.', 220.00, 6, '/uploads/products/Ciao Churu Chicken Fillet Cat Treats 14gx4 (SC-73) (2 packs).png', 24),
(39, 'Kit Cat Kitty Crunch Chicken Cat Treats 60g', 'Irresistible crunchy bites that help clean teeth. Rich in Omega 3 and Omega 6.', 89.00, 6, '/uploads/products/Kit Cat Kitty Crunch Chicken Cat Treats 60g.png', 47);
-- ========================================
-- CART SYSTEM - Guest and Authenticated Users
-- ========================================

CREATE TABLE `guestcart` (
  `session_id` varchar(100) NOT NULL,
  `product_id` int(11) NOT NULL,
  `quantity` int(11) DEFAULT 1,
  `created_at` datetime DEFAULT current_timestamp(),
  CONSTRAINT `guestcart_product_fk` FOREIGN KEY (`product_id`) REFERENCES `products` (`product_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE `cart` (
  `cart_id` int(11) NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `user_id` int(11) NOT NULL,
  `created_at` datetime DEFAULT current_timestamp(),
  CONSTRAINT `cart_user_fk` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE `cartitems` (
  `cart_item_id` int(11) NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `cart_id` int(11) NOT NULL,
  `product_id` int(11) NOT NULL,
  `quantity` int(11) DEFAULT 1,
  UNIQUE KEY `unique_cart_product` (`cart_id`,`product_id`),
  KEY `product_id` (`product_id`),
  CONSTRAINT `cartitems_cart_fk` FOREIGN KEY (`cart_id`) REFERENCES `cart` (`cart_id`) ON DELETE CASCADE,
  CONSTRAINT `cartitems_product_fk` FOREIGN KEY (`product_id`) REFERENCES `products` (`product_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- ========================================
-- ORDER SYSTEM
-- ========================================

CREATE TABLE `inventories` (
  `inventory_id` int(11) NOT NULL PRIMARY KEY,
  `product_id` int(11) NOT NULL,
  `quantity` int(11) NOT NULL,
  KEY `product_id` (`product_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

INSERT INTO `inventories` (`inventory_id`, `product_id`, `quantity`) VALUES
(1, 1, 10),
(2, 2, 10),
(3, 3, 10),
(4, 4, 10),
(5, 5, 10),
(6, 6, 10),
(7, 7, 10),
(8, 8, 10),
(9, 9, 10),
(10, 10, 10),
(11, 11, 10),
(12, 12, 10),
(13, 13, 10),
(14, 14, 10),
(15, 15, 10),
(16, 16, 10);

CREATE TABLE `orders` (
  `order_id` int(11) NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `user_id` int(11),
  `order_date` datetime DEFAULT current_timestamp(),
  `status` enum('Pending','Processing','Shipped','Delivered','Cancelled') DEFAULT 'Pending',
  `total_amount` decimal(10,2) NOT NULL,
  `delivery_address` text NOT NULL,
  `tracking_number` varchar(100),
  `decline_reason` text,
  `created_at` datetime DEFAULT current_timestamp(),
  KEY `user_id` (`user_id`),
  CONSTRAINT `orders_user_fk` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE `orderitems` (
  `order_item_id` int(11) NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `order_id` int(11) NOT NULL,
  `product_id` int(11) NOT NULL,
  `quantity` int(11) NOT NULL,
  `price_at_purchase` decimal(10,2) NOT NULL,
  `sub_total` decimal(10,2) NOT NULL,
  `created_at` datetime DEFAULT current_timestamp(),
  KEY `order_id` (`order_id`),
  KEY `product_id` (`product_id`),
  CONSTRAINT `orderitems_order_fk` FOREIGN KEY (`order_id`) REFERENCES `orders` (`order_id`) ON DELETE CASCADE,
  CONSTRAINT `orderitems_product_fk` FOREIGN KEY (`product_id`) REFERENCES `products` (`product_id`) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE `order_status_history` (
  `status_id` int(11) NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `order_id` int(11) NOT NULL,
  `status` enum('Pending','Processing','Shipped','Delivered','Cancelled') DEFAULT 'Pending',
  `changed_at` datetime DEFAULT current_timestamp(),
  KEY `order_id` (`order_id`),
  CONSTRAINT `order_status_history_order_fk` FOREIGN KEY (`order_id`) REFERENCES `orders` (`order_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE `payments` (
  `payment_id` int(11) NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `order_id` int(11) NOT NULL,
  `method` enum('OL','COD') NOT NULL,
  `status` enum('Paid','Unpaid','Verified') DEFAULT 'Unpaid',
  `payment_proof` text,
  `created_at` datetime DEFAULT current_timestamp(),
  KEY `order_id` (`order_id`),
  CONSTRAINT `payments_order_fk` FOREIGN KEY (`order_id`) REFERENCES `orders` (`order_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE `contact_messages` (
  `id` int(11) NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `name` varchar(255) NOT NULL,
  `email` varchar(255) NOT NULL,
  `subject` varchar(255) NOT NULL,
  `message` text NOT NULL,
  `status` varchar(50) DEFAULT 'new',
  `created_at` datetime DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- ========================================
-- COMMIT AND RESTORE SETTINGS
-- ========================================

COMMIT;
SET FOREIGN_KEY_CHECKS = 1;
SET AUTOCOMMIT = 1;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;