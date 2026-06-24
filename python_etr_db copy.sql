-- Clean Unified E-Commerce Database Schema
-- Consolidates location hierarchy, user management, cart/checkout, and order tracking

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

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
  KEY `province_id` (`province_id`)
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
  KEY `municipality_id` (`municipality_id`)
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
  KEY `idx_role` (`role`)
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
  `description` text,
  `visible` tinyint(4) DEFAULT 1
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- INSERT INTO `categories` (`category_id`, `name`, `description`) VALUES
-- (1, 'Aglaonema', 'A popular indoor plant known for its vibrant foliage'),
-- (2, 'Air Purifying Plants', 'Plants that help filter and clean indoor air'),
-- (3, 'Anthurium', 'A tropical plant valued for its glossy leaves and striking flowers'),
-- (4, 'Beginner-friendly', 'Easy-to-care-for plants suitable for new plant owners'),
-- (9, 'Cacti', 'Low-maintenance succulent plants');

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
  KEY `category_fk` (`category`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- INSERT INTO `products` (`product_id`, `name`, `description`, `price`, `category`, `img_path`, `stock`) VALUES
-- (1, 'Aglaonema Super Red', 'The Aglaonema is an adorable plant with leaves resembling vegetables, originating from the Aglaonema family. It is perfect as a tabletop plant.', 1100.00, 1, '/uploads/products/aglaonema_super_red.jpg', 10),
-- (2, 'Aglaonema Super White', 'The Aglaonema is an adorable plant with leaves resembling vegetables, originating from the Aglaonema family. It is perfect as a tabletop plant.', 1100.00, 1, '/uploads/products/aglaonema_super_white.jpg', 10),
-- (3, 'Aglaonema White Edge', 'The Aglaonema is an adorable plant with leaves resembling vegetables, originating from the Aglaonema family', 1500.00, 1, '/uploads/products/aglaonema_white_edge.jpg', 10),
-- (4, 'Aglaonema Hongmai', 'The Aglaonema is an adorable plant with leaves resembling vegetables, originating from the Aglaonema family. It is perfect as a tabletop plant.', 1100.00, 1, '/uploads/products/aglaonema_hongmai.jpg', 10),
-- (5, 'Calathea Orbifolia', 'Calathea Orbifolia is a stunning tropical houseplant prized for its large, round leaves adorned with silvery-green stripes.', 990.00, 2, '/uploads/products/Calathea_Orbifolia.jpg', 10),
-- (6, 'Zz Raven', 'The Raven ZZ plant is one of the new and rare varieties of plants. It features bright green new growth which matures to a rich purple-black dark foliage.', 1900.00, 2, '/uploads/products/Zz_Raven.jpg', 10),
-- (7, 'Everfresh Tree', 'The Ever Fresh Tree, a native of Japan, is renowned for its lush foliage and graceful silhouette.', 800.00, 2, '/uploads/products/Everfresh_Tree.jpg', 10),
-- (8, 'Ponytail Palm', 'The Ponytail Palm is a unique and eye-catching plant that looks like a miniature tree with a thick, bulbous trunk and long, curly, strap-like leaves.', 3500.00, 2, '/uploads/products/Ponytail_Palm.jpg', 10),
-- (9, 'Anthurium Clarinervium', 'Anthurium clarinervium, also known as the Velvet Cardboard Anthurium, is a stunning plant cherished for its unique foliage.', 450.00, 3, '/uploads/products/Anthurium_Clarinervium.jpg', 10),
-- (10, 'Anthurium Red', 'Anthurium Red, often known as the Flamingo Flower or Laceleaf, is a popular ornamental plant celebrated for its glossy, heart-shaped red spathes.', 600.00, 3, '/uploads/products/Anthurium_Red.jpg', 10),
-- (11, 'Anthurium Pink', 'Anthurium Pink is a charming variety of the Anthurium genus, known for its soft pink spathes that symbolize grace and elegance.', 600.00, 3, '/uploads/products/Anthurium_Pink.jpg', 10),
-- (12, 'Anthurium Clarinervium Foliage', 'Anthurium Clarinervium is a stunning foliage plant admired for its velvety, dark green leaves with striking white veins.', 1750.00, 3, '/uploads/products/Anthurium_Clarinervium_2.jpg', 10),
-- (13, 'Anthurium Crystallinum', 'Anthurium Crystallinum is another jewel-like foliage plant, closely related to Clarinervium, with velvety leaves and prominent white veining.', 1990.00, 3, '/uploads/products/Anthurium_Crystallinum.jpg', 10),
-- (14, 'Sansevieria Bacularis', 'The Sansevieria Bacularis is the best plant for novice plant owners because it is almost indestructible.', 200.00, 4, '/uploads/products/Sansevieria_Bacularis.jpg', 10),
-- (15, 'Fortune Plant', 'The Fortune Plant was aptly named because it creates a cheerful appearance to the atmosphere. It is easy to take care of and can survive best indoors.', 950.00, 4, '/uploads/products/Fortune_Plant.jpg', 10),
-- (16, 'Heartleaf Philodendron', 'The Philodendron Heartleaf is a vining plant that has fast-growing heart-shaped leaves that are dark and glossy green.', 220.00, 4, '/uploads/products/Heartleaf_Philodendron.jpg', 10),
-- (32, 'Cactus', 'Low-maintenance succulent plant', 1599.12, 9, '/uploads/products/cactus.jpg', 20);
-- ========================================
-- PET FOOD PRODUCTS INSERT STATEMENTS
-- ========================================
-- ========================================
-- PET FOOD PRODUCTS INSERT STATEMENTS
-- ========================================

INSERT INTO `products` (`product_id`, `name`, `description`, `price`, `category`, `img_path`, `stock`) VALUES

-- DOG FOOD PRODUCTS (Category 1)
(1, 'Special Delight Adult Smoked Chicken with Mixed Veggies Wet Dog Food 130g (10 pouches)', 'Formulated with high quality ingredients. Offers essential vitamins, minerals and high-quality protein for muscle maintenance and energy.', 350.00, 1, '/uploads/products/Special Delight Adult Smoked Chicken with Mixed Veggies Wet Dog Food 130g (10 pouches).png', 50),
(2, 'Special Delight Adult Salmon Flavor Chunk in Gravy Wet Dog Food 130g (10 pouches)', 'Rich in omega-3 fatty acids, packed with Vitamin D and B vitamins. Promotes strong bones and healthy immune system.', 350.00, 1, '/uploads/products/Special Delight Adult Salmon Flavor Chunk in Gravy Wet Dog Food 130g (10 pouches).png', 50),
(3, 'Special Delight Puppy Roast Beef Chunk in Gravy Wet Dog Food 130g (10 pouches)', 'Made with premium ingredients for growing puppies. Packed with Iron, Zinc, and B vitamins for muscle development and growth.', 350.00, 1, '/uploads/products/Special Delight Puppy Roast Beef Chunk in Gravy Wet Dog Food 130g (10 pouches).png', 50),
(4, 'Special Delight Adult Roast Beef Chunk in Gravy Wet Dog Food 130g (10 pouches)', 'Packed with vital nutrients like Iron, Zinc, and B vitamins. Supports immune function and healthy skin for overall vitality.', 350.00, 1, '/uploads/products/Special Delight Adult Roast Beef Chunk in Gravy Wet Dog Food 130g (10 pouches).png', 50),
(5, 'Special Delight Adult Chicken Chunk in Gravy Wet Dog Food 130g (10 pouches)', 'Good source of high-quality protein essential for muscle maintenance. Savory gravy makes the food highly appealing to pets.', 350.00, 1, '/uploads/products/Special Delight Adult Chicken Chunk in Gravy Wet Dog Food 130g (10 pouches).png', 50),
(6, 'Pedigree Adult Beef Chunks in Gravy Wet Dog Food 130g (12 pouches)', 'Complete and balanced nutrition with Omega 6, Zinc, Calcium and Phosphorous. Provides strong muscles, healthy coat and digestive support.', 492.00, 1, '/uploads/products/Pedigree Adult Beef Chunks in Gravy Wet Dog Food 130g (12 pouches).png', 40),
(7, 'Pedigree Adult Beef Wet Dog Food 400g (3 cans)', 'Home Style recipe with quality meat and vegetables. Enriched with Vitamin E and Omega 6 for healthy skin and beautiful coat.', 375.00, 1, '/uploads/products/Pedigree Adult Beef Wet Dog Food 400g (3 cans).png', 40),
(8, 'Pedigree Adult Chicken and Liver with Gravy Wet Dog Food 130g (12 pouches)', 'Complete nutrition with meaty chunks in gravy. Contains essential vitamins, minerals and protein for overall health.', 492.00, 1, '/uploads/products/Pedigree Adult Chicken and Liver with Gravy Wet Dog Food 130g (12 pouches).png', 40),
(9, 'Pedigree Puppy Chicken Chunks in Gravy Wet Dog Food 130g (12 pouches)', 'Complete and balanced nutrition for puppies. Supports growth with Omega 6, Zinc, Calcium and essential vitamins.', 540.00, 1, '/uploads/products/Pedigree Puppy Chicken Chunks in Gravy Wet Dog Food 130g (12 pouches).png', 40),
(10, 'Pedigree Puppy Wet Dog Food 400g (3 cans)', 'Home Style recipe for puppies with quality meat and vegetables. Enriched with Vitamin E and Omega 6 for healthy development.', 390.00, 1, '/uploads/products/Pedigree Puppy Wet Dog Food 400g (3 cans).png', 40),
(11, 'Pedigree Adult Chicken and Liver Wet Dog Food 400g (3 cans)', 'Home Style chicken recipe with quality ingredients. Provides superb taste and complete nutrition with Vitamin E and Omega 6.', 375.00, 1, '/uploads/products/Pedigree Adult Chicken and Liver Wet Dog Food 400g (3 cans).png', 40),

-- MILK & MILK REPLACERS (Category 2)
(12, 'Cosi Pet\'s Milk 1L (2 cartons)', 'Lactose-free milk for cats and dogs of all breeds. Made from Australian cow\'s milk, suitable for mammalian pets.', 400.00, 2, '/uploads/products/Cosi Pet\'s Milk 1L (2 cartons).png', 30),
(13, 'Puppy Sure Goat\'s Milk Replacer 250g', 'Highly digestible goat\'s milk replacer with low lactose. Rich in vitamins, minerals, enzymes and fatty acids for puppies and kittens.', 719.00, 2, '/uploads/products/Puppy Sure Goat\'s Milk Replacer 250g.png', 25),

-- DRY CAT FOOD (Category 3)
(14, 'Royal Canin Feline Care Nutrition Adult Urinary Care Dry Cat Food 2kg', 'Precisely balanced formula for urinary tract health. Maintains healthy urine concentration and reduces risk of urinary stones.', 1550.00, 3, '/uploads/products/Royal Canin Feline Care Nutrition Adult Urinary Care Dry Cat Food 2kg.png', 30),
(15, 'SmartHeart Adult Chicken and Tuna Dry Cat Food 1.2kg', 'Complete nutrition with DHA for brain function, Omega 3 for healthy heart, and Taurine for vision. Promotes healthy skin and coat.', 310.00, 3, '/uploads/products/SmartHeart Adult Chicken and Tuna Dry Cat Food 1.2kg.png', 45),
(16, 'Royal Canin Feline Care Nutrition Adult Hair and Skin Dry Cat Food 2kg', 'Supports healthy skin and shiny coat with exclusive nutrient complex. Contains Omega-3 and Omega-6 fatty acids.', 1550.00, 3, '/uploads/products/Royal Canin Feline Care Nutrition Adult Hair and Skin Dry Cat Food 2kg.png', 30),
(17, 'Royal Canin Feline Health Nutrition Adult Indoor 27 Dry Cat Food 2kg', 'For indoor cats with moderate calorie content. Reduces stool odour, helps eliminate hairballs and maintains urinary health.', 1360.00, 3, '/uploads/products/Royal Canin Feline Health Nutrition Adult Indoor 27 Dry Cat Food 2kg.png', 30),
(18, 'SmartHeart Kitten Chicken Fresh Egg and Milk Dry Cat Food 1.1kg', 'Complete nutrition for kittens with DHA, Omega 3, and protein from eggs and milk for proper development and growth.', 320.00, 3, '/uploads/products/SmartHeart Kitten Chicken Fresh Egg and Milk Dry Cat Food 1.1kg.png', 45),
(19, 'Royal Canin Feline Health Nutrition Kitten Dry Cat Food 2kg', 'For kittens up to 12 months. Supports digestive health, immune system and healthy growth with adapted nutrients.', 1550.00, 3, '/uploads/products/Royal Canin Feline Health Nutrition Kitten Dry Cat Food 2kg.png', 30),

-- WET CAT FOOD (Category 4)
(20, 'Sheba Succulent Chicken Breast Wet Cat Food 85g (6 cans)', 'Delicate fine flakes in delicious gravy. No artificial colors, flavors or preservatives. Made with finest flaked pieces.', 420.00, 4, '/uploads/products/Sheba Succulent Chicken Breast Wet Cat Food 85g (6 cans).png', 50),
(21, 'SmartHeart Refine Adult Tuna with Crab Stick in Jelly Wet Cat Food 70g (12 pouches)', 'Premium white meat tuna with no artificial colors or preservatives. Gourmet recipe with refined texture and structure.', 504.00, 4, '/uploads/products/SmartHeart Refine Adult Tuna with Crab Stick in Jelly Wet Cat Food 70g (12 pouches).png', 50),
(22, 'SmartHeart Refine Adult Tuna with Bonito in Jelly Wet Cat Food 70g (12 pouches)', 'Selected premium white meat tuna prepared in gourmet recipe. High nutrition and quality for fine dining experience.', 504.00, 4, '/uploads/products/SmartHeart Refine Adult Tuna with Bonito in Jelly Wet Cat Food 70g (12 pouches).png', 50),
(23, 'Sheba Adult Tuna and Salmon Wet Cat Food 70g (12 pouches)', 'Complete and balanced food with delicate flakes in gravy. No artificial colors, flavors or preservatives added.', 540.00, 4, '/uploads/products/Sheba Adult Tuna and Salmon Wet Cat Food 70g (12 pouches).png', 50),
(24, 'Kit Cat Grain-Free Tuna and Mackerel Wet Cat Food 400g (2 cans)', 'Grain-free with hairball control. Rich in Omega 3 and 6, reduces risk of kidney stones and urinary tract infection.', 190.00, 4, '/uploads/products/Kit Cat Grain-Free Tuna and Mackerel Wet Cat Food 400g (2 cans).png', 40),
(25, 'Kit Cat Deboned Chicken and Beef Wet Cat Food 80g (6 cans)', 'Grain-free with Taurine added for all life stages. Supports pH balance and reduces risk of kidney stones.', 354.00, 4, '/uploads/products/Kit Cat Deboned Chicken and Beef Wet Cat Food 80g (6 cans).png', 40),
(26, 'Kit Cat Grain-Free Tuna and Katsoubushi Wet Cat Food 400g (2 cans)', 'Naturally formulated with essential vitamins for eye health and urinary tract prevention. Human grade quality.', 190.00, 4, '/uploads/products/Kit Cat Grain-Free Tuna and Katsoubushi Wet Cat Food 400g (2 cans).png', 40),

-- DOG TREATS (Category 5)
(27, 'Pedigree Dentastix Puppy 4-12 Months Dog Treats 7s 56g (2 packs)', 'Unique X-Shape dental treats for puppies. With anti-tartar ingredients, high calcium, low fat and no sugar added.', 158.00, 5, '/uploads/products/Pedigree Dentastix Puppy 4-12 Months Dog Treats 7s 56g (2 packs).png', 60),
(28, 'SmartHeart Fruit and Vegetable Dog Treats 100g', 'With Omega 3 and 6, prebiotics and natural cellulose. Special shape helps reduce plaque and tartar buildup.', 85.00, 5, '/uploads/products/SmartHeart Fruit and Vegetable Dog Treats 100g.png', 70),
(29, 'Absolute Holistic Dental Chew Peanut Butter Dog Treats 25g', 'Uniquely shaped with 360° nubs and ridges to clean teeth down to gum line. Grain-free with healthy peanut butter.', 49.00, 5, '/uploads/products/Absolute Holistic Dental Chew Peanut Butter Dog Treats 25g.png', 80),
(30, 'SmartHeart Grilled Beef Dog Treats 100g', 'Grilled beef flavor with Omega 6 and natural cellulose. Special shape reduces plaque and tartar for fresh breath.', 85.00, 5, '/uploads/products/SmartHeart Grilled Beef Dog Treats 100g.png', 70),
(31, 'Absolute Holistic Dental Chew Milk Dog Treats 25g', 'Dental chew with milk for calcium and Vitamin D. Grain-free design cleans teeth while strengthening bones.', 49.00, 5, '/uploads/products/Absolute Holistic Dental Chew Milk Dog Treats 25g.png', 80),
(32, 'SmartHeart Grilled Chicken Dog Treats 100g', 'Grilled chicken flavor promoting healthy skin and coat. Natural cellulose supports digestive system health.', 85.00, 5, '/uploads/products/SmartHeart Grilled Chicken Dog Treats 100g.png', 70),
(33, 'Pedigree Dentastix Toy 2-5kg Dog Treats 7s 60g (2 packs)', 'For toy breed dogs 2-5kg. Reduces tartar buildup, cleans hard to reach teeth and supports gum health.', 178.00, 5, '/uploads/products/Pedigree Dentastix Toy 2-5kg Dog Treats 7s 60g (2 packs).png', 60),

-- CAT TREATS (Category 6)
(34, 'Temptations Salmon Cat Treats 75g', 'Crunchy outer shell with soft center. 100% nutritionally complete and balanced. No artificial flavors, re-sealable pouch.', 115.00, 6, '/uploads/products/Temptations Salmon Cat Treats 75g.png', 70),
(35, 'Temptations Chicken Cat Treats 75g', 'Scrumptious crunchy treats with irresistibly soft center. 100% nutritionally complete with real chicken flavor.', 115.00, 6, '/uploads/products/Temptations Chicken Cat Treats 75g.png', 70),
(36, 'Ciao Churu Grilled Tuna Scallop Cat Treats 12gx4 (4R-105) (2 packs)', 'For all life stages with Vitamin E and Green Tea extract. Supports oral health and provides instant nutrition.', 220.00, 6, '/uploads/products/Ciao Churu Grilled Tuna Scallop Cat Treats 12gx4 (4R-105) (2 packs).png', 60),
(37, 'Ciao Churu Tuna Maguro Cat Treats 14gx4 (SC-71) (2 packs)', 'Lickable puree treats with Vitamin E antioxidant. Green Tea fortified for oral support and healthier teeth.', 220.00, 6, '/uploads/products/Ciao Churu Tuna Maguro Cat Treats 14gx4 (SC-71) (2 packs).png', 60),
(38, 'Ciao Churu Chicken Fillet Cat Treats 14gx4 (SC-73) (2 packs)', 'Chicken fillet puree with Vitamin E and Green Tea. Helps reduce cholesterol and provides oral health support.', 220.00, 6, '/uploads/products/Ciao Churu Chicken Fillet Cat Treats 14gx4 (SC-73) (2 packs).png', 60),
(39, 'Kit Cat Kitty Crunch Chicken Cat Treats 60g', 'Crunchy bites in 4 fun shapes with Omega 3 and 6. Taurine added, helps clean teeth and control hairballs.', 89.00, 6, '/uploads/products/Kit Cat Kitty Crunch Chicken Cat Treats 60g.png', 70);-- ========================================
-- CART SYSTEM - Guest and Authenticated Users
-- ========================================

CREATE TABLE `guestcart` (
  `session_id` varchar(100) NOT NULL,
  `product_id` int(11) NOT NULL,
  `quantity` int(11) DEFAULT 1,
  `created_at` datetime DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE `cart` (
  `cart_id` int(11) NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `user_id` int(11) NOT NULL,
  `created_at` datetime DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE `cartitems` (
  `cart_item_id` int(11) NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `cart_id` int(11) NOT NULL,
  `product_id` int(11) NOT NULL,
  `quantity` int(11) DEFAULT 1,
  UNIQUE KEY `unique_cart_product` (`cart_id`,`product_id`),
  KEY `product_id` (`product_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- ========================================
-- ORDER SYSTEM
-- ========================================

CREATE TABLE `inventories` (
  `inventory_id` int(11) NOT NULL,
  `product_id` int(11) NOT NULL,
  `quantity` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `inventories`
--

INSERT INTO `inventories` (`inventory_id`, `product_id`, `quantity`) VALUES
(1, 1, 50),
(2, 2, 50),
(3, 3, 50),
(4, 4, 50),
(5, 5, 50),
(6, 6, 40),
(7, 7, 40),
(8, 8, 40),
(9, 9, 40),
(10, 10, 40),
(11, 11, 40),
(12, 12, 30),
(13, 13, 25),
(14, 14, 30),
(15, 15, 45),
(16, 16, 30),
(17, 17, 30),
(18, 18, 45),
(19, 19, 30),
(20, 20, 50),
(21, 21, 50),
(22, 22, 50),
(23, 23, 50),
(24, 24, 40),
(25, 25, 40),
(26, 26, 40),
(27, 27, 60),
(28, 28, 70),
(29, 29, 80),
(30, 30, 70),
(31, 31, 80),
(32, 32, 70),
(33, 33, 60),
(34, 34, 70),
(35, 35, 70),
(36, 36, 60),
(37, 37, 60),
(38, 38, 60),
(39, 39, 70);

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
  KEY `user_id` (`user_id`)
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
  KEY `product_id` (`product_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE `order_status_history` (
  `status_id` int(11) NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `order_id` int(11) NOT NULL,
  `status` enum('Pending','Processing','Shipped','Delivered','Cancelled') DEFAULT 'Pending',
  `changed_at` datetime DEFAULT current_timestamp(),
  KEY `order_id` (`order_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE `payments` (
  `payment_id` int(11) NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `order_id` int(11) NOT NULL,
  `method` enum('OL','COD') NOT NULL,
  `status` enum('Paid','Unpaid','Verified') DEFAULT 'Unpaid',
  `payment_proof` text,
  `created_at` datetime DEFAULT current_timestamp(),
  KEY `order_id` (`order_id`)
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
-- PRIMARY KEYS
-- ========================================

-- Indexes are now defined in CREATE TABLE statements above

-- ========================================
-- AUTO_INCREMENT
-- ========================================

ALTER TABLE `cart` MODIFY `cart_id` int(11) NOT NULL AUTO_INCREMENT;
ALTER TABLE `cartitems` MODIFY `cart_item_id` int(11) NOT NULL AUTO_INCREMENT;
ALTER TABLE `orders` MODIFY `order_id` int(11) NOT NULL AUTO_INCREMENT;
ALTER TABLE `orderitems` MODIFY `order_item_id` int(11) NOT NULL AUTO_INCREMENT;
ALTER TABLE `order_status_history` MODIFY `status_id` int(11) NOT NULL AUTO_INCREMENT;
ALTER TABLE `payments` MODIFY `payment_id` int(11) NOT NULL AUTO_INCREMENT;
ALTER TABLE `products` MODIFY `product_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=34;
ALTER TABLE `users` MODIFY `user_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=17;
ALTER TABLE `provinces` MODIFY `province_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=5;
ALTER TABLE `municipalities` MODIFY `municipality_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=78;
ALTER TABLE `barangays` MODIFY `barangay_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=771;
ALTER TABLE `contact_messages` MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

-- ========================================
-- FOREIGN KEY CONSTRAINTS
-- ========================================

ALTER TABLE `municipalities` ADD CONSTRAINT `municipalities_ibfk_1` FOREIGN KEY (`province_id`) REFERENCES `provinces` (`province_id`) ON DELETE RESTRICT;
ALTER TABLE `barangays` ADD CONSTRAINT `barangays_ibfk_1` FOREIGN KEY (`municipality_id`) REFERENCES `municipalities` (`municipality_id`) ON DELETE RESTRICT;
ALTER TABLE `users` 
  ADD CONSTRAINT `users_province_fk` FOREIGN KEY (`province`) REFERENCES `provinces` (`province_id`) ON DELETE RESTRICT,
  ADD CONSTRAINT `users_municipality_fk` FOREIGN KEY (`municipality`) REFERENCES `municipalities` (`municipality_id`) ON DELETE RESTRICT,
  ADD CONSTRAINT `users_barangay_fk` FOREIGN KEY (`barangay`) REFERENCES `barangays` (`barangay_id`) ON DELETE RESTRICT;
  
ALTER TABLE `products` ADD CONSTRAINT `products_category_fk` FOREIGN KEY (`category`) REFERENCES `categories` (`category_id`) ON DELETE RESTRICT;
ALTER TABLE `guestcart` ADD CONSTRAINT `guestcart_product_fk` FOREIGN KEY (`product_id`) REFERENCES `products` (`product_id`) ON DELETE CASCADE;
ALTER TABLE `cart` ADD CONSTRAINT `cart_user_fk` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE;
ALTER TABLE `cartitems` 
  ADD CONSTRAINT `cartitems_cart_fk` FOREIGN KEY (`cart_id`) REFERENCES `cart` (`cart_id`) ON DELETE CASCADE,
  ADD CONSTRAINT `cartitems_product_fk` FOREIGN KEY (`product_id`) REFERENCES `products` (`product_id`) ON DELETE CASCADE;
  
ALTER TABLE `orders` ADD CONSTRAINT `orders_user_fk` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE SET NULL;
ALTER TABLE `orderitems` 
  ADD CONSTRAINT `orderitems_order_fk` FOREIGN KEY (`order_id`) REFERENCES `orders` (`order_id`) ON DELETE CASCADE,
  ADD CONSTRAINT `orderitems_product_fk` FOREIGN KEY (`product_id`) REFERENCES `products` (`product_id`) ON DELETE RESTRICT;
  
ALTER TABLE `order_status_history` ADD CONSTRAINT `order_status_history_order_fk` FOREIGN KEY (`order_id`) REFERENCES `orders` (`order_id`) ON DELETE CASCADE;
ALTER TABLE `payments` ADD CONSTRAINT `payments_order_fk` FOREIGN KEY (`order_id`) REFERENCES `orders` (`order_id`) ON DELETE CASCADE;
--
-- Indexes for table `inventories`
--
ALTER TABLE `inventories`
  ADD PRIMARY KEY (`inventory_id`),
  ADD KEY `product_id` (`product_id`);

COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;