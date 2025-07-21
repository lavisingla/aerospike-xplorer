package com.example.aerospike.cache.model;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;
import java.util.Map;

/**
 * User model - contains nested objects (Address) and collections
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class User {
    private Integer id;
    private String name;
    private String email;
    private Address address;
    private List<String> phoneNumbers;
    private Map<String, String> attributes;
    
    // Additional nested objects can be added here
    private List<Order> orders;
    
    /**
     * Order nested class - demonstrates multiple levels of nesting
     */
    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class Order {
        private String orderId;
        private String productName;
        private double price;
        private String status;
    }
}
