import os
import requests
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

API_URL = "https://raw.githubusercontent.com/stivenson/students-api/master/students.json"
CHART_PATH = os.path.join(os.path.dirname(__file__), "student_scores.png")


def fetch_student_scores(url):
    response = requests.get(url, timeout=10)
    response.raise_for_status()

    data = response.json()
    if not isinstance(data, dict) or "students" not in data:
        raise ValueError("Unexpected JSON format: 'students' key not found")

    students = []
    for record in data["students"]:
        name = record.get("name")
        grades = record.get("grades")

        if not name or not isinstance(grades, list) or len(grades) == 0:
            continue

        valid_grades = [float(g) for g in grades if isinstance(g, (int, float))]
        if not valid_grades:
            continue

        avg_grade = sum(valid_grades) / len(valid_grades)
        students.append({
            "name": name,
            "grades": valid_grades,
            "average_score": round(avg_grade, 2),
        })

    if not students:
        raise ValueError("No valid student score records found")

    return students


def calculate_overall_average(students):
    total = sum(student["average_score"] for student in students)
    return total / len(students)


def save_bar_chart(students, overall_average, output_path):
    names = [student["name"] for student in students]
    scores = [student["average_score"] for student in students]

    plt.figure(figsize=(9, 5))
    bars = plt.bar(names, scores, color="#4C78A8", edgecolor="#2F4B7C", width=0.55)

    # Show overall average line for comparison
    plt.axhline(
        y=overall_average,
        color="#E45756",
        linestyle="--",
        linewidth=1.5,
        label=f"Overall Average: {overall_average:.2f}",
    )

    # Display exact score above each bar
    for bar, score in zip(bars, scores):
        plt.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.08,
            f"{score:.2f}",
            ha="center",
            va="bottom",
            fontsize=9,
        )

    plt.title("Student Average Scores")
    plt.xlabel("Student")
    plt.ylabel("Average Score (out of 5.0)")
    plt.ylim(0, 5.8)
    plt.grid(axis="y", linestyle=":", alpha=0.6)
    plt.legend()
    plt.tight_layout()

    plt.savefig(output_path, dpi=150)
    plt.close()


def main():
    try:
        print("Fetching student scores from API...")
        students = fetch_student_scores(API_URL)
    except requests.exceptions.Timeout:
        print("Error: Request timed out while fetching student scores.")
        return
    except requests.exceptions.HTTPError as e:
        print(f"HTTP error occurred: {e}")
        return
    except requests.exceptions.RequestException as e:
        print(f"Network error occurred: {e}")
        return
    except ValueError as e:
        print(f"Error parsing API response: {e}")
        return

    overall_avg = calculate_overall_average(students)

    print("\nParsed Student Scores:")
    for student in students:
        print(
            f"- {student['name']}: grades={student['grades']}, "
            f"average={student['average_score']:.2f}"
        )
    print(f"\nOverall Average Score (across {len(students)} students): {overall_avg:.2f}")

    try:
        save_bar_chart(students, overall_avg, CHART_PATH)
        print(f"Bar chart saved to: {CHART_PATH}")
    except OSError as e:
        print(f"Failed to save chart image: {e}")


if __name__ == "__main__":
    main()
