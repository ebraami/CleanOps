import numpy as np

print("=" * 60)
print("PART 1: NumPy Consolidation Task")
print("=" * 60)

# 1. Array Construction
print("\n--- 1. Array Construction ---")
data_cube = np.array([
    [[1, 2, 3], [4, 5, 6]],
    [[7, 8, 9], [10, 11, 12]]
])
print("data_cube:\n", data_cube)
print("Number of dimensions (ndim):", data_cube.ndim)
print("Shape:", data_cube.shape)

# 2. Indexing & Slicing
print("\n--- 2. Indexing & Slicing ---")
# Access a single specific element: matrix 0, row 1, column 2
single_element = data_cube[0, 1, 2]
print("Single element data_cube[0, 1, 2]:", single_element)

# First row of the second matrix (index 1) in the cube
row_slice = data_cube[1, 0, :]
print("First row of second matrix data_cube[1, 0, :]:", row_slice)

# 3. Data Type Conversion
print("\n--- 3. Data Type Conversion ---")
str_array = np.array(["10.5", "20.7", "30.9"])
print("Original string array:", str_array, "| dtype:", str_array.dtype)

float_array = str_array.astype(float)
print("Converted to float:", float_array, "| dtype:", float_array.dtype)

int_array = float_array.astype(int)
print("Converted to int:", int_array, "| dtype:", int_array.dtype)

# 4. Memory Management (Copy vs View)
print("\n--- 4. Memory Management (Copy vs View) ---")
original = np.array([1, 2, 3, 4, 5])
print("Original array before view modification:", original)

view_array = original.view()
view_array[0] = 999

print("View array after modification:", view_array)
print("Original array after modifying the view:", original)
print("-> Notice the original array changed too, because a view shares memory with its base.")


print("\n" + "=" * 60)
print("PART 2: Sensor Data Management System (Capstone)")
print("=" * 60)


class Sensor:
    """Base class modeling a generic sensor."""

    def __init__(self, sensor_id, firmware_version):
        self.sensor_id = sensor_id           # public attribute
        self.__firmware_version = firmware_version  # private attribute (name-mangled)

    def get_firmware(self):
        """Public method to access the private firmware version."""
        return self.__firmware_version


class TemperatureSensor(Sensor):
    """Subclass specialized for temperature readings."""

    def process_readings(self, raw_data):
        """
        Takes a list or NumPy array of values, converts them to a
        NumPy array of floats, and returns it.
        """
        return np.array(raw_data, dtype=float)


# --- Data Processing (NumPy) ---
print("\n--- Data Processing ---")
batch1 = np.array([20.5, 22.1, 19.8])
batch2 = np.array([21.0, 23.4, 20.2])

combined = np.concatenate((batch1, batch2))
print("Concatenated array:", combined)

reading_matrix = combined.reshape(2, 3)
print("Reshaped (2, 3) matrix (rows = batches, cols = readings):\n", reading_matrix)

# --- Using the OOP classes ---
print("\n--- Using the Sensor Classes ---")
temp_sensor = TemperatureSensor("TS-001", "v1.2.3")
print("Sensor ID:", temp_sensor.sensor_id)
print("Firmware version (via get_firmware):", temp_sensor.get_firmware())

processed = temp_sensor.process_readings([18, 19.5, 20])
print("Processed readings (as float array):", processed, "| dtype:", processed.dtype)

# --- Analysis ---
print("\n--- Analysis ---")
print("Printing every reading using np.nditer:")
for reading in np.nditer(reading_matrix):
    print(reading, end="  ")
print()

print("\nAverage reading per batch (row):")
for i, row in enumerate(reading_matrix):
    avg = row.mean()  # equivalent to np.mean(reading_matrix[i, :])
    print(f"Batch {i + 1} average: {avg:.2f}")

# Alternative one-liner using slicing/axis-based mean:
row_averages = reading_matrix.mean(axis=1)
print("\nAll batch averages at once (axis=1):", row_averages)
