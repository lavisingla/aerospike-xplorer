package com.example.aerospike.cache.util;

import com.example.aerospike.cache.model.Security;

import java.time.LocalDate;
import java.util.ArrayList;
import java.util.List;
import java.util.Random;
import java.util.UUID;
import java.util.concurrent.ThreadLocalRandom;

/**
 * Utility class for generating random Security objects for testing
 */
public class SecurityGenerator {

    private static final String[] SECURITY_NAMES = {
            "Apple Inc.", "Microsoft Corp.", "Amazon.com Inc.", "Alphabet Inc.", "Facebook Inc.",
            "Tesla Inc.", "Berkshire Hathaway", "JPMorgan Chase", "Johnson & Johnson", "Visa Inc.",
            "Procter & Gamble", "Mastercard Inc.", "Bank of America", "Walmart Inc.", "UnitedHealth Group"
    };

    private static final String[] TICKERS = {
            "AAPL", "MSFT", "AMZN", "GOOGL", "FB", "TSLA", "BRK.A", "JPM", "JNJ", "V",
            "PG", "MA", "BAC", "WMT", "UNH"
    };

    private static final String[] BLOOMBERG_CODES = {
            "AAPL US", "MSFT US", "AMZN US", "GOOGL US", "FB US", "TSLA US", "BRK/A US",
            "JPM US", "JNJ US", "V US", "PG US", "MA US", "BAC US", "WMT US", "UNH US"
    };

    private static final Random random = new Random();

    /**
     * Generates a list of random Security objects
     *
     * @param count Number of Security objects to generate
     * @return List of randomly generated Security objects
     */
    public static List<Security> generateRandomSecurities(int count) {
        List<Security> securities = new ArrayList<>(count);
        
        for (int i = 0; i < count; i++) {
            securities.add(generateRandomSecurity(i + 1));
        }
        
        return securities;
    }

    /**
     * Generates a single random Security object
     *
     * @param spn The unique identifier for the security
     * @return A randomly generated Security object
     */
    public static Security generateRandomSecurity(int spn) {
        int nameIndex = random.nextInt(SECURITY_NAMES.length);
        
        Security security = Security.builder()
                .spn(spn)
                .desname(SECURITY_NAMES[nameIndex])
                .shortDesc("Short description for " + SECURITY_NAMES[nameIndex])
                .foTypeId(random.nextInt(20) + 1)
                .subtypeId(random.nextInt(50) + 1)
                .pricingTypeId(random.nextInt(10) + 1)
                .marketId(random.nextInt(100) + 1)
                .countryId(random.nextInt(200) + 1)
                .currencyId(random.nextInt(50) + 1)
                .birthDate(generateRandomDate(2000, 2020))
                .deathDate(generateRandomDate(2023, 2030))
                .creationDate(LocalDate.now().minusDays(random.nextInt(365)))
                .settlementDate(LocalDate.now().plusDays(random.nextInt(30)))
                .local(TICKERS[nameIndex])
                .ric(TICKERS[nameIndex] + ".O")
                .bloomberg(BLOOMBERG_CODES[nameIndex])
                .bbgCompositeId(UUID.randomUUID().toString().substring(0, 10))
                .cusip(generateRandomAlphanumeric(9))
                .isin("US" + generateRandomAlphanumeric(10))
                .sedol(generateRandomAlphanumeric(7))
                .ticker(TICKERS[nameIndex])
                .parent(random.nextInt(1000) + 1)
                .underlying(random.nextInt(1000) + 1)
                .issuerSpn(random.nextInt(1000) + 1)
                .tickUnit(random.nextDouble() * 0.25)
                .minIncrement(random.nextDouble() * 0.1)
                .tradingFactor(1.0 + random.nextDouble())
                .pricingFactor(1.0 + random.nextDouble())
                .isTraded(random.nextBoolean())
                .paysDividend(random.nextBoolean())
                .isListed(random.nextBoolean())
                .build();
        
        // Add 20 random attributes
        for (int i = 1; i <= 20; i++) {
            security.addAttribute("random" + i, generateRandomAttributeValue());
        }
        
        return security;
    }
    
    /**
     * Generates a random date between the specified years
     */
    private static LocalDate generateRandomDate(int startYear, int endYear) {
        int year = startYear + random.nextInt(endYear - startYear + 1);
        int month = 1 + random.nextInt(12);
        int day = 1 + random.nextInt(28); // Avoiding month length issues
        
        return LocalDate.of(year, month, day);
    }
    
    /**
     * Generates a random alphanumeric string of the specified length
     */
    private static String generateRandomAlphanumeric(int length) {
        String chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789";
        StringBuilder sb = new StringBuilder();
        
        for (int i = 0; i < length; i++) {
            sb.append(chars.charAt(random.nextInt(chars.length())));
        }
        
        return sb.toString();
    }
    
    /**
     * Generates a random attribute value of various types
     */
    private static Object generateRandomAttributeValue() {
        int type = random.nextInt(5);
        
        switch (type) {
            case 0:
                return random.nextInt(10000); // Integer
            case 1:
                return random.nextDouble() * 1000; // Double
            case 2:
                return random.nextBoolean(); // Boolean
            case 3:
                return UUID.randomUUID().toString().substring(0, 8); // Short String
            default:
                return LocalDate.now().plusDays(random.nextInt(365)); // Date
        }
    }
}
