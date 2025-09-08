# Dealership Order Processing Methods - 36 Active Dealerships

## Order Processing Types Explained

### **CAO-SCHEDULED (Comparative Analysis Order)**
- **Automated processing** using dealership-specific VIN logs
- System compares current inventory against VIN history
- Only processes vehicles NOT previously processed
- **15 dealerships** use this method

### **MANUAL (LIST Orders)**  
- **Account manager provides specific vehicle lists**
- No automated comparison needed
- Direct processing of provided vehicles
- **21 dealerships** use this method

---

## CAO-SCHEDULED Dealerships (15 Total)

These dealerships use **automated CAO processing** with VIN log comparison:

1. **Auffenberg Hyundai** - Local, ShortCut Pack coverage
2. **Frank Leta Honda** - Local, ShortCut Pack coverage, Y program ($1,650 PPM)
3. **Glendale CDJR** - Local, ShortCut Pack coverage, Custom program
4. **Honda of Frontenac** - Local, ShortCut Pack coverage, Custom program
5. **HW Kia** - Local, ShortCut Pack coverage, Custom program (~$500 PPM)
6. **Pappas Toyota** - Local, Custom coverage, Custom program
7. **Porsche St. Louis** - Local, ShortCut coverage, Custom program
8. **Serra Honda O'Fallon** - Local, ShortCut Pack coverage
9. **South County DCJR** - Non-Local, ShortCut Pack coverage, Custom program
10. **Spirit Lexus** - Local, Custom coverage, Custom program **NOTE: Will NOT be doing typical CAO**
11. **Suntrup Buick GMC** - Local, Flyout coverage (Used Disinterest status) **NOTE: USED FLYOUTS - Will have its own modal, no standard output needed**
12. **Suntrup Ford Kirkwood** - Local, Flyout coverage, Y program ($440 PPM) **NOTE: Will NOT be doing typical CAO**
13. **Suntrup Ford West** - Local, ShortCut Pack coverage, Y program ($440 PPM)
14. **Thoroughbred Ford** - Direct, ShortCut Pack coverage
15. **Weber Chevrolet** - Local, Custom coverage

---

## MANUAL/LIST Order Dealerships (21 Total)

These dealerships use **manual LIST processing** with account manager-provided vehicle lists:

### **BMW Network (2 dealerships)**
1. **BMW of Columbia** - Non-Local, ShortCut Pack coverage
2. **BMW West St. Louis** - Local, ShortCut Pack coverage, Y program ($1,200 PPM) *(TRANSITIONING status)*

### **Bommarito Network (2 dealerships)**
3. **Bommarito Cadillac** - Local, ShortCut Pack coverage, Custom program
4. **Bommarito West County** - Local, Flyout coverage, Custom program *(Pricing Conflict status)*

### **Honda Network (1 dealership)**
5. **Columbia Honda** - Non-Local, ShortCut Pack coverage

### **Dave Sinclair Lincoln Network (2 dealerships)**
6. **Dave Sinclair Lincoln** - Local, ShortCut Pack coverage, Y program ($750 PPM) *(TRANSITIONING status)*
7. **Dave Sinclair Lincoln St. Peters** - Local, None coverage, Y program ($760 PPM)

### **Joe Machens Network (4 dealerships)**
8. **Joe Machens CDJR** - Non-Local, ShortCut Pack coverage
9. **Joe Machens Hyundai** - Non-Local *(incomplete setup data)*
10. **Joe Machens Nissan** - Non-Local, ShortCut Pack coverage
11. **Joe Machens Toyota** - Non-Local, ShortCut Pack coverage

### **Other Premium/Specialty Brands (4 dealerships)**
12. **Indigo Auto Group** - Direct, ShortCut Pack coverage, N program
13. **Jaguar Rancho Mirage** - Direct, None coverage, N program
14. **KIA of Columbia** - Non-Local, ShortCut Pack coverage
15. **Land Rover Rancho Mirage** - Direct, None coverage, N program

### **Local Network Dealerships (6 dealerships)**
16. **Mini of St. Louis** - Local, Flyout coverage, Y program ($500 PPM)
17. **Pundmann Ford** - Local, ShortCut Pack coverage, Y program ($1,350 PPM)
18. **Rusty Drewing Chevy BGMC** - Non-Local, ShortCut Pack coverage
19. **Rusty Drewing Cadillac** - Non-Local, None coverage
20. **Suntrup Hyundai South** - Local, None coverage, Custom program
21. **Suntrup Kia South** - Local, None coverage, Y program ($900 PPM)

---

## Status Classifications

### **Active Dealerships (33)**
- Standard operational status
- No special handling required

### **Transitioning Dealerships (3)**
- **BMW West St. Louis** - Currently transitioning processes
- **Dave Sinclair Lincoln** - Currently transitioning processes  
- **Frank Leta Honda** - Currently transitioning processes
- **HW Kia** - Currently transitioning processes

### **Special Status (1)**
- **Bommarito West County** - Pricing Conflict status
- **Suntrup Buick GMC** - Used Disinterest status

---

## Coverage Types

### **ShortCut Pack** (Most Common)
- Standard coverage package
- Used by majority of dealerships

### **Custom Coverage**
- Premium dealerships with custom arrangements
- Higher service levels

### **Flyout Coverage**
- Specific coverage type for select locations
- Bommarito West County, Mini of St. Louis, Suntrup Buick GMC, Suntrup Ford Kirkwood

### **None Coverage**
- Minimal coverage arrangements
- Dave Sinclair Lincoln St. Peters, Jaguar/Land Rover Rancho Mirage, Rusty Drewing Cadillac, Suntrup Hyundai/Kia South

---

## Monthly Program Status

### **Y Program Dealerships (10 total)**
- Active monthly programs with specified PPM rates
- Range from $440-$1,650 PPM

### **Custom Program Dealerships (9 total)**
- Custom arrangements outside standard PPM structure

### **N Program Dealerships (3 total)**
- No monthly programs
- Direct/Rancho Mirage locations

---

## System Implementation Priority

### **High Priority - CAO-SCHEDULED (15 dealerships)**
- **Working:** Porsche St. Louis, South County DCJR, Frank Leta Honda, HW Kia
- **Needs Fix:** Honda of Frontenac (27 VINs → 11 VINs filtering issue)
- **Remaining 10:** Need CAO testing and validation

### **Medium Priority - MANUAL/LIST (21 dealerships)**
- LIST processing workflow already functional
- Account manager-driven process
- Less automation complexity

*Last Updated: September 5, 2025*