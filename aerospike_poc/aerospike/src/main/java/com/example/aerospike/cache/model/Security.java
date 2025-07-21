package com.example.aerospike.cache.model;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDate;
import java.util.HashMap;
import java.util.Map;

/**
 * Simplified Security model for Aerospike POC
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class Security {
    // Core identifiers
    private int spn;
    private String desname;
    private String shortDesc;
    
    // Type information
    private Integer foTypeId;
    private Integer subtypeId;
    private Integer pricingTypeId;
    
    // Market information
    private Integer marketId;
    private Integer countryId;
    private Integer currencyId;
    
    // Dates
    private LocalDate birthDate;
    private LocalDate deathDate;
    private LocalDate creationDate;
    private LocalDate settlementDate;
    
    // Public identifiers
    private String local;
    private String ric;
    private String bloomberg;
    private String bbgCompositeId;
    private String cusip;
    private String isin;
    private String sedol;
    private String ticker;
    
    // Relationships
    private Integer parent;
    private Integer underlying;
    private Integer issuerSpn;
    
    // Pricing information
    private Double tickUnit;
    private Double minIncrement;
    private Double tradingFactor;
    private Double pricingFactor;
    
    // Flags
    private Boolean isTraded;
    private Boolean paysDividend;
    private Boolean isListed;
    
    // Additional attributes
    private Map<String, Object> attributes;
    
    /**
     * Adds an attribute to the security
     */
    public void addAttribute(String name, Object value) {
        if (attributes == null) {
            attributes = new HashMap<>();
        }
        attributes.put(name, value);
    }
    
    /**
     * Gets an attribute value
     */
    public Object getAttribute(String name) {
        return attributes != null ? attributes.get(name) : null;
    }
    
    /**
     * Returns true if the security is valid (not cancelled)
     */
    public boolean isValid() {
        return valid;
    }
    
    /**
     * Returns true if the security is live (death date is after today)
     */
    public boolean isLive() {
        return live;
    }

    public boolean valid;
    public boolean live;
}
