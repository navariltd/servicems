## **Service Management System (Service MS)**

The Service MS is an end-to-end custom [Frappe](https://frappe.io/framework) application designed to streamline operations in automotive service centers and garages. It centralizes customer management, vehicle records, service jobs, parts inventory, billing, and reporting into a single, efficient workflow. The application extends [ERPNext](https://frappe.io/erpnext) capabilities to small and mid-sized garages seeking improved operational control, transparency, and customer satisfaction.

<img width="1828" height="891" alt="image" src="https://github.com/user-attachments/assets/4706d47a-63f8-4c96-a38b-f1e8cd310fa6" />

---

## **Core Features** ⚙️
-	**Service Booking** 📅: Capture customer service requests in advance and Schedule service date and preferred workshop/bay
-	**Service Vehicle Inspection** 🔍: Perform initial vehicle inspection upon arrival
-	**Service Job Card (SJC)** 🧾: Create a service job card from Service Booking 
-	**Tasks and Tasks Assignments**🛠️
-	**Material Requisitions and Stock Entries**📦: Request required spare parts and consumables, and do stock entries
-	**Quotation and Billing**💰: Create Quotation and Sales Invoice

## **Configurations**🧩
1.	**Service MS Settings** ⚙️
- Default Item Groups for parts and consumables
- Default Item Pricelist
- Auto-generation of Sales invoice on job card submission
- Default purpose of Material Request (Draft/Submitted)
- Default stock entry type for stock entry
- Whether to use spares or items
- Default Cost Center

2.	**Masters** 🗂️ 
- Workshop and Bay set up
- Define Customers
- Define Service Vehicle
- Define Spares/Items

---
  	
## **Benefits**🎯
- Streamline service operations
- Control spare parts and consumables
-	Ensure accurate billing and stock movement
-	Improve visibility and control over service operations
-	Reduce manual paperwork and data duplication
-	Enhance customer experience through timely updates and accurate billing
- Enable data-driven decisions via real-time reports

---

## **Workflow** 🔄

  <img width="611" height="621" alt="Service MS drawio" src="https://github.com/user-attachments/assets/0c3b7899-c011-4868-98e2-bc77f3373d97" />

---
##**Usage Guide**🤵🏿

1. **Service Booking**
   Prerequisites: Customer, Service Vehicle, Workshop, and Bay
   <img width="796" height="437" alt="image" src="https://github.com/user-attachments/assets/05e6f011-ebd9-48b5-9e39-6a4ed2bc1775" />

- Navigate to Service Booking
- Add new Service Booking
- Select Customer, Service Vehicle, Workshop, Bay, and set the Booking time and date.
- Describe the service in the service description
- Save and Submit

  or
<img width="1798" height="862" alt="image" src="https://github.com/user-attachments/assets/fc4a61aa-296c-42db-9fda-ee8d2073dddf" />

- Navigate to the Booking page
- Select the Service day and Bay
- Tap the add button on the selected date and bay
- Select Customer, Service Vehicle, Workshop, Bay, and set the Booking time
- Describe the service in the service description
- Tap create
- Note: Only use checkbox is new customer and is new vehicle when booking a new service vehicle for a new customer. 
        New section for customer details and vehicle details will pop up
    
  
  

   
2.  **Service Job Card**

- Create Service Jobcard from a Service Booking
- Company will be fetched from service settings or session defaults
- Receiving date will be auto-filled as the posting date of the service job card
- Pricelist and Cost Center will be fetched from service settings
- Booking details will be  auto-fetched from the Service Booking
  
<img width="1264" height="724" alt="image" src="https://github.com/user-attachments/assets/064cfa3a-6017-48a5-a470-a1e352fbdf05" />
    
- Fill Complaints table - these are the service vehicle problems as specified by the driver or customer
- Fill Faults table - these are the problems found on the vehicle by the mechanic or the garage attendant after vehicle inspection
  <img width="1285" height="440" alt="image" src="https://github.com/user-attachments/assets/f3296abd-4e00-4c8f-a136-8b39cb271812" />

- On Service Charge Template select a predefined service template and put the chargeable rate, tick is billable to later bill the customer
  <img width="1248" height="251" alt="image" src="https://github.com/user-attachments/assets/e7f1d9d5-e43c-4a99-8728-1ba20e91af18" />

- You Can also create a new service charge template from above table
  <img width="1534" height="862" alt="image" src="https://github.com/user-attachments/assets/231fe811-d88f-4a29-a52b-b52502f75cf6" />
  Choose a non stock item on item. Choose whether this item is billable. The pricelist is auto-fetched from the service setting.
  Add all tasks to be done and choose user to assign each task in service task template.
  Select a list of items/spares and the quantity required to complete the tasks and choose whether to bill them through checkbox is billable on Service Template Parts and Consumable.
  Save the service charge template

  <img width="1250" height="686" alt="image" src="https://github.com/user-attachments/assets/cd5fd7d6-7e6a-4d36-8e7b-f0911660f4d6" />

- Task are auto-fetched from the service charge template. They can also be added on task table manually
- Spares/items to request are also auto-fetched from the service charge template. They can also be added on the table manually
- Save the Service Jobcard.
  The following can be created from create button in Jobcard:
- Quotation
- Stock Entry
- Service Parts Entry: when using spares instead of items
- Material Request
- Vehicle Inspection


  Request for the spares/items to request by creating a material request. The request is fulfilled once a stock entry is created against it. A stock entry can also be created directly from the job card. Once the stock entry is done, complete tasks to submit the service jobcard. On Submit a sales invoice will be autogenerated in draft billing the billable service item and spares/items.




  

  




#### License

MIT
