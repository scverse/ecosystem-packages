# **Reviewing scverse-affiliated packages**

This document outlines the criteria for reviewing packages applying to become scverse-affiliated and is intended for reviewers.

Thank you for participating in the review process for scverse-affiliated package submissions. Your insights and evaluations play a crucial role in maintaining the quality and integrity of the scverse ecosystem.

Unlike a typical academic paper review, your report will be combined with a coordinator's review and may not be directly shared with the authors. Please submit your review report privately to the coordinator who contacted you.

The review focuses on several key areas as detailed below. You are expected to base your review on these criteria, but you are also welcome to highlight any other relevant aspects. For each category, please provide a 'traffic light' rating and include comments, especially where there is room for improvement.

### **Traffic Light Rating System**

- **Red**: <td><img src="https://img.shields.io/badge/Red-red.svg" alt="Red"></td> Indicates major issues or shortcomings. Affiliated packages must resolve any red scores to be accepted or remain listed.
- **Orange**: <td><img src="https://img.shields.io/badge/Orange-orange.svg" alt="Orange"></td> Acceptable but with notable deficiencies. This serves as both a caution to users and a motivator for developers to improve.
- **Green**: <td><img src="https://img.shields.io/badge/Green-brightgreen.svg" alt="Green"></td> Represents the ideal standard. All-green packages may be featured prominently within the scverse ecosystem.

The review categories are as follows, with specific keywords in **`monospaced text`** for use in the scverse registry:

### **Functionality (`'functionality'`)**

Assess whether the package's scope is relevant and useful within the scverse ecosystem.

### **Integration with scverse (`'ecointegration'`)**

Evaluate the package's use of scverse and other related libraries, checking for unnecessary duplication or missed opportunities for integration.

### **License (`'license'`)**

Verify that the the code is publicly available under an OSI-approved licensei

### **Distribution (`'distribution'`)**

Verify that the package can be installed from a standard registry (e.g. PyPI, conda-forge, bioconda)

### **Documentation (`'documentation'`)**

Review the package's documentation for completeness, clarity, and usefulness to potential users.

### **Testing (`'testing'`)**

Consider the coverage and effectiveness of the package's automated tests.

### **Development status (`'devstatus'`)**

Determine the package's current development stage and the versioned releases.

### **Python 3 compatibility (`'python3'`)**

Verify that the package is compatible with Python 3.

---

**Detailed Guidelines for Each Category:**

### **Functionality ('functionality')**

Evaluate the scope of the package:

<td><img src="https://img.shields.io/badge/Red-red.svg" alt="Red"></td> Not relevant to the scverse community.
<td><img src="https://img.shields.io/badge/Green-brightgreen.svg" alt="Green"></td> Broadly useful across the scverse community.

### **Integration with scverse ('ecointegration')**

Assess integration with scverse:

<td><img src="https://img.shields.io/badge/Red-red.svg" alt="Red"></td> Little to no use of scverse structures where applicable.
<td><img src="https://img.shields.io/badge/Green-brightgreen.svg" alt="Green"></td> The package uses scverse datastructures where appropriate (i.e. AnnData, MuData or SpatialData and their modality-specific extensions).

### **License ('license')**

Verify OSI-approved license:

<td><img src="https://img.shields.io/badge/Red-red.svg" alt="Red"></td> Code is not OSI-approved licensed.
<td><img src="https://img.shields.io/badge/Green-brightgreen.svg" alt="Green"></td> Code is OSI-approved licensed.

### **Distribution ('distribution')**

Evaluate the package's documentation:

<td><img src="https://img.shields.io/badge/Red-red.svg" alt="Red"></td> The package cannot be installed from a standard registry.
<td><img src="https://img.shields.io/badge/Green-brightgreen.svg" alt="Green"></td> The package can be installed from a standard registry (e.g. PyPI, conda-forge, bioconda).

### **Documentation ('documentation')**

Evaluate the package's documentation:

<td><img src="https://img.shields.io/badge/Red-red.svg" alt="Red"></td> Inadequate or significantly lacking.
<td><img src="https://img.shields.io/badge/Green-brightgreen.svg" alt="Green"></td> The package provides API documentation via a website or README.

### **Testing ('testing')**

Assess the package's testing practices:

<td><img src="https://img.shields.io/badge/Red-red.svg" alt="Red"></td> Insufficient test coverage or poorly implemented tests.
<td><img src="https://img.shields.io/badge/Green-brightgreen.svg" alt="Green"></td> The package uses automated software tests and runs them via continuous integration (CI).

### **Development status ('devstatus')**

Determine the package's development status:

<td><img src="https://img.shields.io/badge/Red-red.svg" alt="Red"></td> The package does not provide versioned releases.
<td><img src="https://img.shields.io/badge/Green-brightgreen.svg" alt="Green"></td> The package provides versioned releases.

<td><img src="https://img.shields.io/badge/Red-red.svg" alt="Red"></td> Submission by an individual who is neither an author nor a maintainer of the tool or/and does not agree on listing the package on the scverse website. 
<td><img src="https://img.shields.io/badge/Green-brightgreen.svg" alt="Green"></td> Submission by an author or maintainer of the tool who agrees on listing the package on the scverse website.

### **Python 3 compatibility ('python3')**

Check Python 3 compatibility:

<td><img src="https://img.shields.io/badge/Red-red.svg" alt="Red"></td> Not compatible with Python 3.
<td><img src="https://img.shields.io/badge/Green-brightgreen.svg" alt="Green"></td> Fully compatible with Python 3.

