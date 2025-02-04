# Import all necessary libraries
import numpy as np
from modAL.models import ActiveLearner
from modAL.uncertainty import uncertainty_sampling
from sklearn.datasets import load_digits
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
import tkinter as tk
from tkinter import messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# Load dataset and split
n_initial = 100
X, y = load_digits(return_X_y=True)
X_train, X_test, y_train, y_test = train_test_split(X, y)

initial_idx = np.random.choice(range(len(X_train)), size=n_initial, replace=False)
X_initial, y_initial = X_train[initial_idx], y_train[initial_idx]
X_pool, y_pool = np.delete(X_train, initial_idx, axis=0), np.delete(y_train, initial_idx, axis=0)

# Initialize the learner
learner = ActiveLearner(
    estimator=RandomForestClassifier(),
    query_strategy=uncertainty_sampling, # opciones: margin_sampling, entropy_sampling, uncertainty_sampling
    X_training=X_initial, y_training=y_initial
)

n_queries = 10
accuracy_scores = [learner.score(X_test, y_test)]
current_query_idx = None
query_inst = None
query_count = 0

# Functions for GUI
def label_digit():
    global X_pool, y_pool, current_query_idx, query_inst, query_count
    try:
        label = int(entry.get())
        if not (0 <= label <= 9):
            raise ValueError("Please enter a valid digit (0-9).")
        
        # Teach the model
        learner.teach(query_inst.reshape(1, -1), np.array([label], dtype=int))
        
        # Update the pool
        X_pool, y_pool = np.delete(X_pool, current_query_idx, axis=0), np.delete(y_pool, current_query_idx, axis=0)
        
        # Clear the entry box
        entry.delete(0, tk.END)  # Clear the text box

        # Update accuracy scores
        accuracy_scores.append(learner.score(X_test, y_test))
        update_plot()
        query_count += 1

        if query_count < n_queries:
            query_instance()  # Fetch next query
        else:
            messagebox.showinfo("Finished", "Reached the maximum number of queries.")
            root.quit()

    except ValueError as e:
        messagebox.showerror("Error", str(e))

def query_instance():
    global current_query_idx, query_inst
    if len(X_pool) == 0:
        messagebox.showinfo("Finished", "No more data to query.")
        root.quit()
        return
    current_query_idx, query_inst = learner.query(X_pool)
    ax_image.clear()
    ax_image.imshow(query_inst.reshape(8, 8), cmap='gray')
    ax_image.set_title("Digit to Label")
    canvas_image.draw()

def update_plot():
    ax_accuracy.clear()
    ax_accuracy.plot(range(len(accuracy_scores)), accuracy_scores, marker='o')
    ax_accuracy.set_title("Model Accuracy")
    ax_accuracy.set_xlabel("Number of Queries")
    ax_accuracy.set_ylabel("Accuracy")
    canvas_plot.draw()

# Main GUI setup
root = tk.Tk()
root.title("Active Learning Interface")

# Image display
frame_image = tk.Frame(root)
frame_image.pack(side=tk.LEFT, padx=10, pady=10)
fig_image, ax_image = plt.subplots()
ax_image.axis('off')
canvas_image = FigureCanvasTkAgg(fig_image, master=frame_image)
canvas_image.get_tk_widget().pack()

# Accuracy plot
frame_plot = tk.Frame(root)
frame_plot.pack(side=tk.RIGHT, padx=10, pady=10)
fig_plot, ax_accuracy = plt.subplots()
canvas_plot = FigureCanvasTkAgg(fig_plot, master=frame_plot)
canvas_plot.get_tk_widget().pack()

# Controls
frame_controls = tk.Frame(root)
frame_controls.pack(pady=10)
entry = tk.Entry(frame_controls)
entry.pack(side=tk.LEFT)
submit_button = tk.Button(frame_controls, text="Submit", command=label_digit)
submit_button.pack(side=tk.LEFT)

# Start first query
query_instance()

# Run GUI
root.mainloop()