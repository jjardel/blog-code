

types = read.csv( 'orderTypes.out' )
names( types ) = c( "dealerID", "fracMaintenance", "fracRepair" )
cars = read.csv( 'makes.out' )
names( cars ) = c( 'dealerID', 'Make' )

df = join( types, rankings, by = "dealerID" )
data = join( df, cars, by = "dealerID" )
data$Make = factor( data$Make,
  labels = c( "Nissan", "Infiniti", "Other" ) )

nissan = subset( data, Make == 'Nissan' )$fracRepair
infiniti = subset( data, Make == 'Infiniti' )$fracRepair
t.test( nissan, infiniti, alternative = "less" )

png( 'repairHists.png' )
par( mfrow = c( 1, 2 ) )
hist( nissan, xlab = "Fraction of Repairs Requiring Extensive Service",
     main = "Nissan" )
hist( infiniti, xlab = "Fraction of Repairs Requiring Extensive Service",
     main = "Infiniti" )


dev.off()
