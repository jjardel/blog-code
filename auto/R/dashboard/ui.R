library(shiny)

# Define UI for random distribution application 
shinyUI(pageWithSidebar(
    
  # Application title
  headerPanel("Repair Order Data"),
  
  # Sidebar with controls to select the random distribution type
  # and number of observations to generate. Note the use of the br()
  # element to introduce extra vertical spacing
  sidebarPanel(
    #radioButtons("dist", "Distribution type:",
    #             c("Normal" = "norm",
    #               "Uniform" = "unif",
    #               "Log-normal" = "lnorm",
    #               "Exponential" = "exp")),
    #br(),
    
    sliderInput("wVolume", 
                "Volume:", 
                 value = 1,
                 min = 0., 
                 max = 6.,
                 step = 0.1),
               
   sliderInput( "wSales",
                "Sales:",
                value = 1.,
                min = 0.,
                max = 6.,
                step = 0.1 ),
               
   sliderInput( "wEfficiency",
                "Efficiency:",
                value = 1.,
                min = 0.,
                max = 6.,
                step = 0.1 ),
               
   sliderInput( "wOutOfWarranty",
                "Out of Warranty Sales:",
                value = 1.,
                min = 0.,
                max = 6.,
                step = 0.1 ),
               
   sliderInput( "wLoyalty",
                "Customer Loyalty:",
                value = 1.,
                min = 0.,
                max = 6.,
                step = 0.1 ),
               
   sliderInput( "wGrowth",
                "Growth:",
                value = 1.,
                min = 0.,
                max = 6.,
                step = 0.1 )
               
               
   
  ),
  
  
  # Show a tabset that includes a plot, summary, and table view
  # of the generated distribution
  mainPanel(
    tabsetPanel(
      tabPanel("Dealer Performance", tableOutput("ranking"),
               h4( "Top Performing Dealer" ), plotOutput( "spiderweb" )
               ), 
      tabPanel("Clustering", verbatimTextOutput("summary")), 
      tabPanel("Coupon Study", tableOutput("table"))
    )
  )
))
