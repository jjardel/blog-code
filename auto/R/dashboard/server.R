library(shiny)
library( plotrix )
library( plyr )

# Define server logic for random distribution application
shinyServer(function(input, output) {

  performance = read.csv( 'metric1.out' )
  colnames( performance ) = c( "dealerID", "volume", "sales",
            "efficiency", "outOfWarranty", "loyalty", "growth" )
  
  # consider scaling from 0 to 1
  #p = scale( performance[ ,2:7 ] )

  maxs = apply(performance[ ,2:7 ], 2, max)    
  mins = apply(performance[ ,2:7 ], 2, min)
  p = scale( performance[ ,2:7 ], center = mins, scale = maxs - mins)
  #p = transform( p, dealerID = performance$dealerID )
  
  # Reactive expression to generate the requested distribution. This is 
  # called whenever the inputs change. The output functions defined 
  # below then all use the value computed from this expression

  
  weights = reactive({
    getWeights = c( input$wVolume, input$wSales, input$wEfficiency,
      input$wOutOfWarranty, input$wLoyalty, input$wGrowth )
    getWeights
    
  })
  # Generate a plot of the data. Also uses the inputs to build the 
  # plot label. Note that the dependencies on both the inputs and
  # the data reactive expression are both tracked, and all expressions 
  # are called in the sequence implied by the dependency graph
#  output$plot <- renderPlot({
#    dist <- input$dist
#    n <- input$n
#    
#    hist(data(), 
#         main=paste('r', dist, '(', n, ')', sep=''))
#  })

#  topDealerSummary <- reactive({
#    weights = c( input$wVolume, input$wSales, input$wEfficiency,
#      input$wOutOfWarranty, input$wLoyalty, input$wGrowth )

  normalize <- reactive({
    results = p %*% weights() / sum( weights() )
    results = data.frame( dealerID = performance$dealerID, Rating = results )
    results
  })
    
  getTop10 <- reactive({
    results = normalize()
    top10 = results[ with( results, order( -Rating ) ), ]
    top10$Rating = top10$Rating / max( top10$Rating )
    top10 = head( top10, n = 10 )
    ranks = seq( from = 1, to = dim( top10 )[ 1 ], by = 1 )
    row.names( top10 ) = ranks
    names( top10 )[ 1 ] = 'Dealer ID'
    top10
  })
  
  # Generate a summary of the data
  output$ranking <- renderTable({
    top10 = getTop10()
  })

  output$spiderweb <- renderPlot({
    top10 = getTop10()
    topID = top10[ 1, 1 ]

    idx = subset( performance, dealerID == topID )[ 1 ]
    idx = as.integer( row.names( idx ) )
    y = p[ idx, ]
    prettyLabels = c( "Volume", "Sales", "Efficiency",
      "Out of Warranty Sales", "Customer Loyalty", "Growth" )
      
    radial.plot( y, labels = prettyLabels, rp.type="p",
                radial.lim = c( 0, 1), poly.col = "blue" )
    

  })

  output$performance <- renderTable({
    names( performance )[ 1 ] = 'Dealer ID'
    top10 = getTop10()
    topPerformance = join( performance, top10, by = 'Dealer ID', type = 'right' )
    topPerformance$sales = topPerformance$sales / 1000000
    topPerformance$outOfWarranty = topPerformance$outOfWarranty * 100
    topPerformance$loyalty = topPerformance$loyalty * 100
    prettyNames = c( 'Dealer ID', 'Volume (Number of ROs)', 'Sales ($Millions)',
      'Efficiency ( Sales/Labor Time)', 'Percentage Out of Warranty Sales',
    'Percentage Repeat Customers', 'Growth ($Thousands/Quarter)', 'Rating' )
    names( topPerformance ) = prettyNames

    topPerformance
    

  })
  

  # idea: maybe treat this like an optimization problem and try to
  # to find the set of weights that makes the score the largest
  
  # Generate an HTML table view of the data
#  output$table <- renderTable({
#    data.frame(x=data())
#  })
  
})
