# Severity Scoring Requirements

## 1. Purpose

The purpose of the severity score is to give each report a simple severity value based on the detected waste materials.

The system uses a rule-based formula. Each material type has a weight, and the weight is multiplied by the detected quantity of that material.

The final result is the **Severity Score**.

## 2. Severity Formula

The severity score is calculated as a weighted sum of all detected waste materials.

### Formula

```text
Severity Score =
(Quantity of Material 1 × Weight of Material 1)
+ (Quantity of Material 2 × Weight of Material 2)
+ ...
+ (Quantity of Material N × Weight of Material N)
```

For example:

```text
Severity Score =
(Plastic Quantity × Plastic Weight)
+ (Glass Quantity × Glass Weight)
+ (Metal Quantity × Metal Weight)
+ (Organic Quantity × Organic Weight)
```

The formula uses the weight stored in the configurable weight table.

## 3. Weight Table Structure

The material weights should be stored in a separate configurable table. The weights should not be hardcoded in the system.

| Field | Description |
|---|---|
| `material_type` | The type of waste material. |
| `weight` | The severity weight assigned to the material type. |

### Example Weight Table

| material_type | weight |
|---|---:|
| Plastic | 2 |
| Glass | 3 |
| Metal | 4 |
| Organic | 1 |

These values are only example values. They are not final values.

The important requirement is that the system reads the weight from the table instead of keeping the weight directly inside the formula or code.

## 4. Inputs

The severity calculation needs:

1. **Material Type** - the type of waste detected.
2. **Quantity** - the detected amount or count of that material.
3. **Weight** - the weight assigned to the material type in the configurable weight table.

The system uses these inputs to calculate the severity score.

## 5. Output

The main output is:

**Severity Score**

The score is a numeric value calculated from the quantities and weights of the detected waste materials.

For example, if a report has:

- Plastic quantity = 5
- Glass quantity = 2
- Metal quantity = 3

and the example weights are:

- Plastic weight = 2
- Glass weight = 3
- Metal weight = 4

then:

```text
Severity Score =
(5 × 2) + (2 × 3) + (3 × 4)

= 10 + 6 + 12

= 28
```

Therefore, the example severity score is **28**.

## 6. Calculation Steps

1. Get the detected waste materials from the report.
2. Get the quantity of each material.
3. Find the weight of each material from the configurable weight table.
4. Multiply each quantity by its material weight.
5. Add all the results together.
6. Use the final value as the Severity Score.

## 7. Configurable Weights

The weights must be configurable.

This means that the weight of a material can be changed in the weight table without changing the severity formula.

For example, if the weight of Plastic changes from `2` to `3`, the system should use the new value from the table for future calculations.

The formula itself does not need to be changed.

## 8. Provisional Weights

The weights are **provisional** and are pending calibration.

This means the example weights should not be treated as final business values. They can be reviewed and changed after testing and calibration.

> **Note:** The weights are provisional pending calibration and may be changed after the system is tested and calibrated.

## 9. Summary

The severity scoring system uses a simple rule-based weighted sum.

The main requirements are:

- Each detected material has a quantity.
- Each material type has a weight.
- The weights are stored in a configurable table.
- The weights are not hardcoded in the formula.
- The quantity is multiplied by the related material weight.
- All weighted values are added together.
- The final result is the Severity Score.
- The weights are provisional until calibration is completed.

This provides a simple and configurable way to calculate the severity of a report based on the detected waste materials.
