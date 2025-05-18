import subprocess

# === CONFIG ===
script_sequence = [
    "jd_summarizer.py --fast",
    "cv_jd_extractor.py",
    "cv_jd_matching.py",
    "shortlisted_interview_scheduler.py"
]

# === DISPLAY STEPS WITH NUMBERS ===
print("\n📋 Available Steps in Pipeline:")
for idx, script in enumerate(script_sequence, 1):
    print(f"{idx}. {script}")

# === ASK USER WHERE TO START FROM ===
while True:
    try:
        start_index = int(input("\n🔢 Enter step number to start from (1 - {}): ".format(len(script_sequence)))) - 1
        if 0 <= start_index < len(script_sequence):
            break
        else:
            print("⚠️ Invalid number. Try again.")
    except ValueError:
        print("⚠️ Please enter a valid integer.")

# === EXECUTE SCRIPTS FROM SELECTED POINT ===
print("\n🚀 Starting pipeline from Step {}...\n".format(start_index + 1))

i = start_index
while i < len(script_sequence):
    script = script_sequence[i]
    print(f"▶️ Step {i+1}: Running {script}")
    try:
        subprocess.run(["python"] + script.split(), check=True)
        print(f"✅ Completed: {script}\n")
        i += 1
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running {script}: {e}")
        choice = input("💡 Type 'retry' to re-run, 'skip' to move on, or 'exit' to stop: ").strip().lower()
        if choice == "retry":
            continue
        elif choice == "skip":
            i += 1
        elif choice == "exit":
            print("⛔ Pipeline execution stopped by user.")
            break
        else:
            print("⚠️ Invalid input. Skipping to next step.\n")
            i += 1

print("🎯 Pipeline execution finished.")
