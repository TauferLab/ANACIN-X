#ifndef COMM_PATTERN_GENERATOR_COMM_PATTERN_H
#define COMM_PATTERN_GENERATOR_COMM_PATTERN_H

// STL
#include <string>

// Boost
#include "boost/serialization/access.hpp"
#include "boost/serialization/string.hpp" 

struct CommPattern
{
  int n_iters;
  double nd_fraction;
  std::string pattern_name;
  CommPattern( std::string pattern_name, int n_iters, double nd_fraction ) :
    pattern_name(pattern_name), n_iters(n_iters), nd_fraction(nd_fraction) {}

  CommPattern() : pattern_name(""), n_iters(0), nd_fraction(0) {}
  
  // Serialization helper for broadcast 
  //friend class boost::serialization::access;
  template<typename Archive>
  void serialize( Archive& archive, const unsigned int version )
  {
    archive & n_iters;
    archive & nd_fraction;
    archive & pattern_name;
  }
};

#endif
