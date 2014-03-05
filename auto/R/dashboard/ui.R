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
    
   sliderInput( "wSales",
                "Sales:",
                value = 0.2,
                min = 0.,
                max = 1.,
                step = 0.05 ),
               
   sliderInput( "wEfficiency",
                "Efficiency:",
                value = 0.2,
                min = 0.,
                max = 1.,
                step = 0.05 ),
               
   sliderInput( "wOutOfWarranty",
                "Out of Warranty Sales:",
                value = .2,
                min = 0.,
                max = 1.,
                step = 0.05 ),
               
   sliderInput( "wLoyalty",
                "Customer Loyalty:",
                value = 0.2,
                min = 0.,
                max = 1.,
                step = 0.05 ),
               
   sliderInput( "wGrowth",
                "Growth:",
                value = 0.2,
                min = 0.,
                max = 1.,
                step = 0.05 )
               
               
   
  ),
  
  
  # Show a tabset that includes a plot, summary, and table view
  # of the generated distribution
  mainPanel(
    tabsetPanel(
      tabPanel("Dealer Performance", tableOutput( "performance" ),
               verbatimTextOutput( "stats" ),
               h4( "Top Performing Dealer" ), plotOutput( "spiderweb" )
               ),
      tabPanel("Markets", plotOutput("markets") ),
      tabPanel("Order Types", plotOutput("orderTypes") )

#               br(),
#               plotOutput("map" ))
    )
  )
))
