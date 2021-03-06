library(shiny)

# Define server logic for random distribution application
shinyServer(function(input, output) {

  performance = read.csv( 'metric1.out' )
  colnames( performance ) = c( "dealerID", "volume", "sales",
            "efficiency", "outOfWarranty", "loyalty", "growth" )
  
  # consider scaling from 0 to 1
  p = scale( performance[ ,2:7 ] )
  #p = transform( p, dealerID = performance$dealerID )
  
  # Reactive expression to generate the requested distribution. This is 
  # called whenever the inputs change. The output functions defined 
  # below then all use the value computed from this expression

  
  ranking = reactive({
    weights = c( input$wVolume, input$wSales, input$wEfficiency,
      input$wOutOfWarranty, input$wLoyalty, input$wGrowth )
    
    results = p %*% weights / sum( weights )
    results = data.frame( dealerID = performance$dealerID, Rating = results )
    top10 = results[ with( results, order( -Rating ) ), ]
    top10$Rating = top10$Rating / max( top10$Rating )
    top10 = head( top10, n = 10 )
    ranks = seq( from = 1, to = dim( top10 )[ 1 ], by = 1 )
    row.names( top10 ) = ranks
    names( top10 )[ 1 ] = 'Dealer ID'
    top10
    
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

  topDealerSummary <- reactive({
    weights = c( input$wVolume, input$wSales, input$wEfficiency,
      input$wOutOfWarranty, input$wLoyalty, input$wGrowth )
    
  
  # Generate a summary of the data
  output$ranking <- renderTable({
    ranking()
  })

  output$spiderweb <- renderPlot({

  })
  
  # Generate an HTML table view of the data
#  output$table <- renderTable({
#    data.frame(x=data())
#  })
  
})
