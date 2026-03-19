

# **📄 Product Requirements Document (PRD)**

## **Product: Personal Health Daily Tracker**

## **Version: V1**

---

# **1\. Overview**

## **1.1 Purpose**

Build a personal health tracking system that enables users to:

* Authenticate with email-based sign-in  
* Log daily health metrics  
* Track workout completion  
* Track menstrual cycle days (optional)  
* Compare performance against configurable targets  
* Maintain historical consistency even when targets change

The system must balance flexibility (editable history) with evaluation integrity (target snapshot logic).

---

# **2\. Product Goals**

### **Primary Goals**

1. Enable consistent daily health logging.  
2. Support dynamic target management.  
3. Preserve historical evaluation accuracy.  
4. Allow retroactive entry and correction.  
5. Provide per-day performance analysis.  
   ---

   # **3\. Non-Goals (V1 Exclusions)**

* Multi-user collaboration  
* Social features  
* AI-based recommendations  
* Cycle prediction or ovulation forecasting  
* Workout type/intensity tracking  
* Symptom tracking  
* Notifications/reminders  
* Wearable integrations  
  ---

  # **4\. User Persona**

An individual tracking:

* Nutrition (calories, protein)  
* Sleep  
* Workout consistency  
* Menstrual cycle days (optional)

User characteristics:

* May forget to log and add entries later.  
* May adjust targets over time.  
* Wants meaningful evaluation against targets.  
  ---

  # **5\. Core Features (Frozen Scope)**

  ---

  ## **5.1 Daily Log**

Each date can have at most one Daily Log.

### **Daily Log Fields**

Quantitative Metrics:

* Calories (integer)  
* Protein (integer)  
* Sleep (decimal)

Binary Habit Indicators:

* Workout Completed (boolean)  
* Is Period Day (boolean)

Target Snapshot (stored per log):

* Calorie Target  
* Protein Target  
* Sleep Target

Metadata:

* Date  
* Created timestamp  
* Updated timestamp  
  ---

  ## **5.2 Target Management**

User can configure global targets for:

* Calories  
* Protein  
* Sleep

Targets are stored separately from Daily Logs.

---

## **5.3 Target Change Behavior**

When targets are updated:

1. Change takes effect immediately.  
2. Today’s Daily Log snapshot is updated (if it exists).  
3. Future logs use new targets.  
4. Past logs remain unchanged.

This ensures evaluation consistency.

---

## **5.4 Historical Access**

User can:

* Create log for past date.  
* Update existing log for any date.  
* View historical logs by date range.

There is no immutability enforcement in V1.

---

## **5.5 Daily Analysis View**

Each Daily Log includes a dedicated analysis page showing:

### **Performance Evaluation**

* Actual vs Target comparison for:  
  * Calories  
  * Protein  
  * Sleep  
* Delta values  
* Basic status indicators

  ### **Habit Indicators**

* Workout completion status  
* Period day indicator

Evaluation always uses the stored target snapshot for that day.

---

## **5.6 Authentication**

Users authenticate with **email-based Firebase Auth**.

Authentication requirements:

* The frontend handles sign-in using Firebase Authentication  
* The backend accepts Firebase ID tokens on protected requests  
* The backend auto-provisions a local user record on first authenticated use  
* Each authenticated user can access only their own data  

---

# **6\. Functional Requirements (FR)**

---

### **FR1 – Create or Update Daily Log**

System shall allow user to create or update a Daily Log for any date.

---

### **FR2 – Single Log Per Date**

System shall enforce one Daily Log per user per date.

---

### **FR3 – Store Target Snapshot**

System shall store target values inside Daily Log at creation.

---

### **FR4 – Update Daily Log**

System shall allow user to modify:

* Calories  
* Protein  
* Sleep  
* Workout Completed  
* Is Period Day

For any date.

---

### **FR5 – Target Configuration**

System shall allow user to update:

* Calorie Target  
* Protein Target  
* Sleep Target  
  ---

  ### **FR6 – Target Propagation Rule**

If targets are updated:

* Today’s Daily Log snapshot shall be updated.  
* Past logs shall remain unchanged.  
* Future logs shall use new targets.  
  ---

  ### **FR7 – Daily Analysis Generation**

System shall generate analysis for each Daily Log comparing:

* Actual quantitative values  
* Stored target snapshot values  
  ---

  ### **FR8 – Historical Retrieval**

System shall allow retrieval of Daily Logs by date or date range.

---

### **FR9 – Authentication**

System shall require authenticated access using email-based Firebase Authentication and shall scope all data access to the authenticated user.

---

# **7\. Business Rules**

1. Only one Daily Log per date per user.  
2. Snapshot targets must not retroactively change.  
3. All Daily Log updates must be atomic.  
4. Quantitative metrics must be non-negative.  
5. Sleep must allow decimal values.  
6. Workout and Period flags default to false.  
   ---

   # **8\. Non-Functional Requirements (NFR)**

   ---

   ## **8.1 Data Integrity**

* Target snapshot consistency must be preserved.  
* Target changes must not affect historical logs.  
  ---

  ## **8.2 Consistency**

* All updates must be transactional.  
* Daily Log must always contain valid snapshot values.  
  ---

  ## **8.3 Performance**

* Daily Log retrieval must be near-instant.  
* History queries must scale for multi-year data.  
  ---

  ## **8.4 Extensibility**

System must allow future addition of:

* Additional metrics  
* Weekly summaries  
* Trend analytics  
  ---

  ## **8.5 Security**

* API must require authentication.  
* Users must only access their own data.  
  ---

  # **9\. Conceptual Data Model**

  ### **User**

* id
* firebase\_uid
* email
* created\_at

  ### **TargetConfig**

* user\_id  
* calorie\_target  
* protein\_target  
* sleep\_target  
* updated\_at

  ### **DailyLog**

* id  
* user\_id  
* date  
* calories\_actual  
* protein\_actual  
* sleep\_actual  
* workout\_completed (boolean)  
* is\_period\_day (boolean)  
* calorie\_target\_snapshot  
* protein\_target\_snapshot  
* sleep\_target\_snapshot  
* created\_at  
* updated\_at  
  ---

  # **10\. Edge Cases**

1. User changes targets multiple times in a day → latest value applies.  
2. User creates past log → snapshot uses current target at creation time.  
3. User deletes a log → system must allow recreation for that date.  
4. User logs only some fields → remaining fields remain nullable or defaulted.  
   ---

   # **11\. Success Metrics**

* Daily logging frequency  
* Target adjustment frequency  
* 30-day retention  
* % of days with complete data

