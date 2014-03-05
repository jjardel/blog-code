library(shiny)

# Define UI for shiny app
shinyUI(pageWithSidebar(
    
  # Application title
  headerPanel("Repair Order Data"),
  
  # sidebar with weights to set interactively
  sidebarPanel(
    
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
