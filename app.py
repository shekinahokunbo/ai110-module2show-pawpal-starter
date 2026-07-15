import streamlit as st
from diagrams.pawpal_system import Owner, Pet, Scheduler, Task

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")
st.caption("Plan a day of pet care based on time, priority, and preferences.")

# --- Session vault: create the Owner ONCE, then reuse it across reruns. ---
if "owner" not in st.session_state:
    st.session_state.owner = Owner("Jordan")
owner = st.session_state.owner

owner.name = st.text_input("Owner name", value=owner.name)

st.divider()

# --- Add a Pet -------------------------------------------------------------
st.subheader("Add a Pet")
with st.form("add_pet", clear_on_submit=True):
    name = st.text_input("Pet name", value="Mochi")
    species = st.selectbox("Species", ["dog", "cat", "other"])
    breed = st.text_input("Breed", value="")
    age = st.number_input("Age", min_value=0, max_value=40, value=1)
    if st.form_submit_button("Add pet") and name:
        owner.add_pet(Pet(name, species, breed, int(age)))
        st.success(f"Added {name} to {owner.name}'s pets.")

if not owner.pets:
    st.info("Add a pet to start scheduling tasks.")
    st.stop()

st.divider()

# --- Schedule a Task -------------------------------------------------------
st.subheader("Schedule a Task")
with st.form("add_task", clear_on_submit=True):
    pet_choice = st.selectbox("For which pet?", [p.name for p in owner.pets])
    title = st.text_input("Task title", value="Morning walk")
    col1, col2 = st.columns(2)
    duration = col1.number_input("Duration (min)", min_value=1, max_value=240, value=20)
    priority = col2.selectbox("Priority", ["low", "medium", "high"], index=2)
    preferred = st.text_input("Preferred time (HH:MM)", value="07:30")
    if st.form_submit_button("Add task"):
        pet = owner.get_pet(pet_choice)
        pet.add_task(Task(title, "", int(duration),
                          priority=priority, preferred_time=preferred))
        st.success(f"Added '{title}' for {pet_choice}.")

# --- Current pets & tasks --------------------------------------------------
st.markdown("### Pets & Tasks")
for pet in owner.pets:
    st.markdown(f"**{pet.name}** ({pet.animal_type}) — {len(pet.get_tasks())} task(s)")
    for t in pet.get_tasks():
        st.write(f"- {t.name} · {t.duration} min · {t.priority} "
                 f"· prefers {t.preferred_time or 'any time'}")

st.divider()

# --- Build Schedule --------------------------------------------------------
st.subheader("Build Schedule")
col1, col2 = st.columns(2)
available = col1.number_input("Available time (min)", min_value=5, max_value=600, value=60)
start = col2.text_input("Start time (HH:MM)", value="07:00")

if st.button("Generate schedule"):
    scheduler = Scheduler(owner, available_time=int(available), start_time=start)
    plan = scheduler.generate_plan()

    st.markdown("### 📅 Today's Schedule")
    if plan["scheduled_tasks"]:
        for t in plan["scheduled_tasks"]:
            st.write(f"🟢 **{t.start_time}** — {t.name} "
                     f"({t.duration} min, {t.priority})")
    else:
        st.write("Nothing fit in the available time.")

    if plan["skipped_tasks"]:
        st.markdown("**Skipped**")
        for t in plan["skipped_tasks"]:
            st.write(f"⚪ {t.name} — {scheduler.explain_decision(t)}")

    st.caption(f"Time used: {plan['total_scheduled_time']} / "
               f"{plan['total_available_time']} min "
               f"({plan['remaining_time']} min free)")
