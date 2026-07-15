# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.
- What classes did you include, and what responsibilities did you assign to each?

### 1a. Initial Design

For the initial PawPal+ design, I chose four main classes: `Pet`, `CareTask`, `Scheduler`, and `DailyPlan`.

The `Pet` class represents the animal receiving care. It stores basic information such as the pet’s name, animal type, breed, age, and any special needs. Its main responsibility is to keep pet-specific information organized and connect the pet to its care tasks.

The `CareTask` class represents an individual pet care activity, such as feeding, walking, grooming, medication, or enrichment. It stores details including the task name, duration, priority, category, preferred time, and completion status. It is also responsible for actions such as marking a task as completed, updating task information, and determining whether the task fits within the owner’s remaining available time.

The `Scheduler` class contains the main scheduling logic for the system. Its responsibility is to examine the available care tasks, sort them by priority, check the available time, prevent scheduling conflicts, and decide which tasks should be included or skipped. It also explains why each scheduling decision was made.

The `DailyPlan` class represents the completed care schedule for a specific day. It stores the scheduled tasks, skipped tasks, total available time, and total scheduled time. Its responsibility is to organize the scheduler’s results, calculate remaining time, and format the final plan so it can be displayed clearly in the Streamlit interface.

I kept the initial design focused on these four classes to avoid unnecessary complexity. Together, they separate the pet data, task data, scheduling logic, and final schedule into clear responsibilities.


The three core actions a user should be able to perform in PawPal+ are:

1. **Enter owner and pet information**
   The user should be able to provide basic information about themselves and their pet, such as the owner’s name, the pet’s name, animal type, breed, and any important care preferences or needs.

2. **Add and manage pet care tasks**
   The user should be able to create, edit, and remove care tasks such as feeding, walking, medication, grooming, and enrichment. Each task should include information such as its duration and priority level.

3. **Generate and view a daily care plan**
   The user should be able to enter how much time they have available and generate a daily schedule. PawPal+ should prioritize the most important tasks, fit them within the available time, and explain why each task was included or skipped.


**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
