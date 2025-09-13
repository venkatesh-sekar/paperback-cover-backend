def adjust_resolutions(resolutions, target_width_ratio, target_height_ratio):
    target_aspect_ratio = target_width_ratio / target_height_ratio
    detailed_results = []

    # Calculate and adjust aspect ratios for both increasing and decreasing dimensions
    for res in resolutions:
        width, height = map(int, res.split('x'))
        current_aspect_ratio = width / height

        # Adjustments for increasing dimensions
        if current_aspect_ratio < target_aspect_ratio:
            increased_width = int(height * target_aspect_ratio)
            increased_height = height
        else:
            increased_width = width
            increased_height = int(width / target_aspect_ratio)

        increase_width_diff = increased_width - width
        increase_height_diff = increased_height - height

        # Adjustments for decreasing dimensions
        if current_aspect_ratio > target_aspect_ratio:
            decreased_width = int(height * target_aspect_ratio)
            decreased_height = height
        else:
            decreased_width = width
            decreased_height = int(width / target_aspect_ratio)

        decrease_width_diff = decreased_width - width
        decrease_height_diff = decreased_height - height

        detailed_results.append({
            'initial_resolution': f"{width}x{height}",
            'increase_to_width': increased_width,
            'increase_to_height': increased_height,
            'pixels_added_width': increase_width_diff,
            'pixels_added_height': increase_height_diff,
            'decrease_to_width': decreased_width,
            'decrease_to_height': decreased_height,
            'pixels_reduced_width': decrease_width_diff,
            'pixels_reduced_height': decrease_height_diff
        })

    return detailed_results


# Example usage
resolutions = ["1024x1024", "1152x896", "896x1152", "1216x832", "832x1216", "1344x768", "768x1344", "1536x640", "640x1536"]
target_width_ratio = 6
target_height_ratio = 9
results = adjust_resolutions(resolutions, target_width_ratio, target_height_ratio)

# Print results
for result in results:
    print("Initial Resolution:", result['initial_resolution'])
    print("Increase to:", f"{result['increase_to_width']}x{result['increase_to_height']}",
          "| Pixels Added - Width:", result['pixels_added_width'],
          ", Height:", result['pixels_added_height'])
    print("Decrease to:", f"{result['decrease_to_width']}x{result['decrease_to_height']}",
          "| Pixels Reduced - Width:", result['pixels_reduced_width'],
          ", Height:", result['pixels_reduced_height'])
    print()
