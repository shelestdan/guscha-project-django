# Requirements Document

## Introduction

Блок-герой для отображения товара на странице коллекций. Блок представляет собой секцию с информацией о товаре (название, цена, кнопка предзаказа), фотографией модели в геометрической маске и фотографией товара с текстурной рамкой. Все изображения загружаются через админ-панель Django.

## Glossary

- **Product_Hero_Block**: Секция на странице, отображающая информацию о товаре с визуальными элементами
- **Model_Image**: Фотография модели в одежде, отображаемая в геометрической маске (шестиугольник)
- **Product_Image**: Фотография товара отдельно, отображаемая с эффектом текстурной/рваной рамки
- **Preorder_Button**: Кнопка для оформления предзаказа товара
- **Hexagon_Mask**: CSS clip-path маска в форме шестиугольника для фото модели

## Requirements

### Requirement 1

**User Story:** As a visitor, I want to see product information clearly displayed, so that I can understand what product is being showcased.

#### Acceptance Criteria

1. WHEN the Product_Hero_Block loads THEN THE system SHALL display the product name in large bold black typography on the left side
2. WHEN the Product_Hero_Block loads THEN THE system SHALL display the product price in format "X XXX.XX ₽" below the product name
3. WHEN the background color is rendered THEN THE system SHALL use a light beige/cream color (#F5F3EE or similar)

### Requirement 2

**User Story:** As a visitor, I want to see the model wearing the product, so that I can visualize how the product looks when worn.

#### Acceptance Criteria

1. WHEN the Model_Image is displayed THEN THE system SHALL render it inside a hexagonal clip-path mask
2. WHEN the Model_Image is loaded from admin THEN THE system SHALL position it in the center-right area of the block
3. WHEN the Model_Image container is rendered THEN THE system SHALL apply a subtle shadow or depth effect

### Requirement 3

**User Story:** As a visitor, I want to see the product separately, so that I can see the product details without the model.

#### Acceptance Criteria

1. WHEN the Product_Image is displayed THEN THE system SHALL render it with a textured/torn paper edge effect
2. WHEN the Product_Image is loaded from admin THEN THE system SHALL position it to the right of the Model_Image
3. WHEN the Product_Image container is rendered THEN THE system SHALL apply a slight rotation or tilt effect

### Requirement 4

**User Story:** As a visitor, I want to preorder the product, so that I can reserve it before it becomes available.

#### Acceptance Criteria

1. WHEN the Preorder_Button is displayed THEN THE system SHALL render it with a rectangular border and transparent background
2. WHEN a visitor clicks the Preorder_Button THEN THE system SHALL navigate to the preorder flow or trigger preorder action
3. WHEN the Preorder_Button is hovered THEN THE system SHALL provide visual feedback (color change or border highlight)

### Requirement 5

**User Story:** As a visitor, I want to navigate to more details, so that I can learn more about the product.

#### Acceptance Criteria

1. WHEN the navigation arrow is displayed THEN THE system SHALL render a right-pointing arrow (→) below the Preorder_Button
2. WHEN a visitor clicks the navigation arrow THEN THE system SHALL navigate to the product detail page

### Requirement 6

**User Story:** As an admin, I want to upload model and product images through the admin panel, so that I can manage the hero block content.

#### Acceptance Criteria

1. WHEN an admin uploads a Model_Image THEN THE system SHALL store it and make it available for the Product_Hero_Block
2. WHEN an admin uploads a Product_Image THEN THE system SHALL store it and make it available for the Product_Hero_Block
3. WHEN images are updated in admin THEN THE system SHALL reflect changes on the frontend without code changes

### Requirement 7

**User Story:** As a visitor on mobile, I want the block to be responsive, so that I can view it properly on any device.

#### Acceptance Criteria

1. WHEN the viewport width is less than 768px THEN THE system SHALL stack elements vertically
2. WHEN the viewport width is less than 768px THEN THE system SHALL reduce image sizes proportionally
3. WHEN the viewport width is less than 480px THEN THE system SHALL adjust typography sizes for readability
