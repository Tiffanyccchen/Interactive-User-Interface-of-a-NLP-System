# Interactive User Interface of a NLP System
This UI is for the ATS system I developed

## Introduction
[The Demo Video](https://www.youtube.com/watch?v=I4NF0fCviHI)  

The UI Interface

![UI Screen Shot](/static/img/ScreenShot.png)


* Left Panel contains input / output textareas and summary / reset buttons.
* Right Panel consists of 
  1. Keywords areas user can input. They will be included or excluded in the summary.
  2. Check boxes and Radio boxes for setting different aspects' levels of producing a summary.
    For example : Centrality, First Paragraph importance, Redundancy and number of output characters.

## Structure
1. templates / static folders: html file / css and javascript files
2. The Python kernel file connecting the front end, back end, and produces summaries.
3. The Keyword folder contains codes for pretraining doc2vec models, clustering, modeling, and use them to finding keywords in a new document.
3. Reports and readmes for understanding the concepts of summarization algorithms.

## Notice
The whole Python algorithms are not uploaded here because they are being used by a company.  
However, by reading the Reports, you can understand the concepts.
