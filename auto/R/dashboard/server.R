library(shiny)
library( plotrix )
library( plyr )
library( ggplot2 )
library( ggmap )


# Define server logic for shiny app
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
    normalized = results[ with( results, order( -Rating ) ), ]
    normalized$Rating = normalized$Rating / max( normalized$Rating )
    normalized
  })
    
  getTop10 <- reactive({
    results = normalize()
    #write.csv( results, file = 'ranking.csv' )
    top10 = head( results, n = 10 )
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

  # output a table of the 10 best dealers
  output$performance <- renderTable({
    names( performance )[ 1 ] = 'Dealer ID'
    top10 = getTop10()
    topPerformance = join( performance, top10, by = 'Dealer ID', type = 'right' )
    
    topPerformance$sales = topPerformance$sales / 1000000
    topPerformance$outOfWarranty = topPerformance$outOfWarranty * 100
    topPerformance$loyalty = topPerformance$loyalty * 100
    prettyNames = c( 'Dealer ID', 'Sales ($Millions)',
      'Efficiency ( Sales/Labor Time)', 'Percentage Out of Warranty Sales',
    'Percentage Repeat Customers', 'Growth($Thousands/Quarter)', 'Rating' )
    names( topPerformance ) = prettyNames
    topPerformance

  })

    output$stats <- renderPrint({
      # calculate summary stats for best value in each column
      prettyNames = c( 'dealer id', 'Sales',
        'Efficiency', 'Percentage Out of Warranty Sales',
        'Percentage Repeat Customers', 'Growth' )
      performance$sales = performance$sales / 1000000
      performance$outOfWarranty = performance$outOfWarranty * 100
      performance$loyalty = performance$loyalty * 100
      names( performance ) = prettyNames
      
      summary( performance[ ,2:6 ] )


  })


  getMakeData <- reactive({
    # takes the vehicle make data into account
     rankings = normalize()
     types = read.csv( 'orderTypes.out' )
     names( types ) = c( "dealerID", "fracMaintenance", "fracRepair" )

     cars = read.csv( 'makes.out' )
     names( cars ) = c( 'dealerID', 'Make' )

     df = join( types, rankings, by = "dealerID" )
     dfWithCars = join( df, cars, by = "dealerID" )
     dfWithCars$Make = factor( dfWithCars$Make,
       labels = c( "Nissan", "Infiniti", "Other" ) )
     dfWithCars

   })

  output$orderTypes <- renderPlot({
    data = getMakeData()
    names( data )[ 5 ] = "Dealer"
    p = ggplot( data, aes( fracRepair*100, Rating, color = Dealer) ) +
      geom_point() +
      xlab( "Percentage of Service Orders that are Major Repairs" )

  print( p )  

  })

   
  output$markets <- renderPlot({

    # the geo centering didn't work for a few dealers on the east coast
    bad = c( 10467, 7437, 9894, 10728, 15948 )
    data = read.csv( 'market_segs.out' )
    names( data ) <- c( "dealerID", "lat", "lon", "Market" )
    data[ data$dealerID %in% bad, 2:3 ] = NA
    dealers = data

    rankings = normalize()
    allData = join( dealers, rankings, by = 'dealerID', type = 'inner' )

    inds = by( allData, allData$Market, function(X) X[ which.max(X$Rating),])
    bestDealers = do.call( "rbind", inds )
    
    mPerformance = join( performance, dealers, by = 'dealerID', type = 'inner' )
    maxs = apply( mPerformance[ ,2:6 ], 2, max )
    mins = apply( mPerformance[ ,2:6 ], 2, min )

    # scale to [0, 1 ]
    norm = scale( mPerformance[ ,2:6 ], center = mins, scale = maxs - mins)
    norm = as.data.frame( norm )
    names( norm ) = names( mPerformance )[ 2:6 ]

    
    norm$dealerID = mPerformance$dealerID
    norm$Market = mPerformance$Market

    
    #norm = transform( norm, "dealerID" = mPerformance$dealerID )
    #norm = transform( norm, "Market" = mPerformance$Market )

    
    marketNames = c( "Midwest", "West", "Southwest", "Northeast", "Southeast" )
    colors = c( "red", "purple", "blue", "yellow", "green" )

    par( mfrow = c( 2, 3 ) )
    for (i in 1:5) {
      market.frame = apply( subset( norm, Market == i - 1 ), 2, mean )
      radial.plot( market.frame[ 1:5 ],
                  labels = c( "Sales", "Efficiency", "Out of Warranty",
                  "Loyalty", "Growth" ), rp.type="p",
                radial.lim = c( 0, 1), poly.col = colors[ i ],
                  main = marketNames[ i ] )
    }



  })
  
  
})
