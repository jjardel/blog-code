library(shiny)
library( plotrix )
library( plyr )

# Define server logic for random distribution application
shinyServer(function(input, output) {

  performance = read.csv( 'metric1.out' )
  colnames( performance ) = c( "dealerID", "sales",
            "efficiency", "outOfWarranty", "loyalty", "growth" )
  
  # scaling each feature to [0, 1] range

  maxs = apply(performance[ ,2:6 ], 2, max)    
  mins = apply(performance[ ,2:6 ], 2, min)
  p = scale( performance[ ,2:6 ], center = mins, scale = maxs - mins)

  # standard scaling
  #p = scale( performance[ ,2:6 ], center = TRUE, scale = TRUE )
  
  # reactive expression to calculate weights interactively
  weights = reactive({
    getWeights = c( input$wSales, input$wEfficiency,
      input$wOutOfWarranty, input$wLoyalty, input$wGrowth )
    getWeights
    
  })
  
  normalize <- reactive({
    results = p %*% weights() / sum( weights() )
    results = data.frame( dealerID = performance$dealerID, Rating = results )
    results
  })
    
  getTop10 <- reactive({
    results = normalize()
    #write.csv( results, file = 'ranking.csv' )
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
    prettyLabels = c(  "Sales", "Efficiency",
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
    prettyNames = c( 'Dealer ID', 'Sales ($Millions)',
      'Efficiency ( Sales/Labor Time)', 'Percentage Out of Warranty Sales',
    'Percentage Repeat Customers', 'Normalized Growth', 'Rating' )
    names( topPerformance ) = prettyNames
    topPerformance

  })

    output$stats <- renderPrint({
      # calculate summary stats for best value in each column
      prettyNames = c( 'dealer id', 'Sales',
        'Efficiency', 'Percentage Out of Warranty Sales',
        'Percentage Repeat Customers', 'Normalized Growth' )
      performance$sales = performance$sales / 1000000
      performance$outOfWarranty = performance$outOfWarranty * 100
      performance$loyalty = performance$loyalty * 100
      names( performance ) = prettyNames
      
      summary( performance[ ,2:6 ] )


  })
  

  # idea: maybe treat this like an optimization problem and try to
  # to find the set of weights that makes the score the largest
  
  # Generate an HTML table view of the data
#  output$table <- renderTable({
#    data.frame(x=data())
#  })
  
})
