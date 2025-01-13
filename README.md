# Bank_statement_summary
This personal project aims to analyze my account statements easily and automatically.

This project is a collaboration between me and ChatGPT because I don't code in Python yet, and this language was the most suitable for the project.
The steps are as follows:
First program: Read, clean, and sort the information.
  - From an Excel account statement file, generate a JSON file that will contain all the cleaned and categorized information.
  - Another JSON file is also generated, containing the labels to which the user has assigned a category (e.g., taxes, fuel, groceries) and a recurrence type (fixed, recurring, occasional). This file enables the automatic assignment of categories and recurrence types to similar labels in the same Excel document or future Excel documents.
Second program: Generate a summary.
  -  Calculate and display the sum of fixed debits, fixed credits, and the remaining balance.
  -  Calculate and display the proportions of each category within the fixed debits and fixed credits.
  -  Similarly, calculate and display the proportions of each category within recurring and occasional expenses.
The next steps will be as follows:
  - Combine multiple Excel files to generate a JSON file in order to create monthly summaries.
  - Create a user interface to make the program usable by everyone.
  - Improve my Python skills to clean up the code.
