#ifndef COMM_PATTERN_GENERATOR_COMM_PATTERN_H
#define COMM_PATTERN_GENERATOR_COMM_PATTERN_H

// STL
#include <string>

// Boost
#include "boost/serialization/access.hpp"
#include "boost/serialization/string.hpp" 
#include "boost/serialization/unordered_map.hpp" 

struct CommPattern
{
  int n_iters;
  double nd_fraction;
  std::string pattern_name;
  std::unordered_map<std::string,int> params;

  CommPattern( std::string pattern_name, 
               int n_iters, 
               double nd_fraction,
               std::unordered_map<std::string,int> params 
             ) : pattern_name(pattern_name), 
                 n_iters(n_iters), 
                 nd_fraction(nd_fraction),
                 params(params) {}

  //CommPattern() : pattern_name(""), n_iters(0), nd_fraction(0) {}
  CommPattern() {}
  
  // Serialization helper for broadcast 
  template<typename Archive>
  void serialize( Archive& archive, const unsigned int version )
  {
    archive & n_iters;
    archive & nd_fraction;
    archive & pattern_name;
    archive & params;
  }
};

#endif
